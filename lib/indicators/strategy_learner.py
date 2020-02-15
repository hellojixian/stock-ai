import os, sys, json
import numpy as np
import pandas as pd
import progressbar
import multiprocessing as mp
import datetime
import itertools
import hashlib

POP_SIZE = 30 #40
NEW_KIDS = 70 #60
DNA_LEN = 26
MUT_STRENGTH = 0.3
POOL = None
DNA_MIN, DNA_MAX = -5,5
MAX_MAIN_PROCESSES = 30
MAX_SUB_PROCESSES = 10

def _init_globals(bar_size, counter):
    global pbar_size,processed_DNA, start_ts
    start_ts = datetime.datetime.now(tz=None)
    pbar_size = bar_size
    processed_DNA  = counter
    return

class StrategyLearner(object):
    """动态策略的一个学习器"""

    def __init__(self, strategy):
        super().__init__()
        self.strategy = strategy
        self.settings_filename = os.path.join('data','knowledgebase','{}-settings.json'.format(strategy.NAME))
        self.reset()
        self.load()

    def reset(self):
        self.pop = []
        self.pop_size = POP_SIZE
        self.n_kids = NEW_KIDS
        self.mut_strength = MUT_STRENGTH
        self.old_training_score = None
        self.old_validation_score = None
        self.stop_improving_counter = 0
        if len(self.pop)==0: self.pop = self.gen_DNAset()
        return

    def gen_DNAset(self):
        dna_list = []
        DNA_LEN = self.strategy.DNA_LEN
        for i in range(self.pop_size):
            dna_list.append(np.random.randn(DNA_LEN)-0.5)
        dna_list = np.array(dna_list)
        return dna_list

    def make_kids(self):
        DNA_LEN = self.strategy.DNA_LEN
        kids = np.empty((self.n_kids, DNA_LEN))
        for kid in kids:
            p1, p2 = np.random.choice(np.arange(len(self.pop)), size=2, replace=False)
            cp = np.random.randint(0, 2, DNA_LEN, dtype=np.bool)

            kid[cp] = self.pop[p1, cp]
            kid[~cp] = self.pop[p2, ~cp]
            # mutation
            for i in range(DNA_LEN):
                mut = int(np.random.uniform(-self.mut_strength,self.mut_strength))
                v = kid[i] + mut
                kid[i] = np.clip(v, DNA_MIN, DNA_MAX)
        return kids

    def kill_bad(self, kids):
        self.pop = np.vstack((self.pop, kids))
        fitness = self.get_fitness(self.pop)            # calculate global fitness
        idx = np.arange(self.pop.shape[0])
        good_idx = idx[fitness.argsort()][-self.pop_size:]   # selected by fitness ranking (not value)
        self.pop = self.pop[good_idx]
        return

    def get_fitness(self, dna_series):
        global POOL, start_ts
        start_ts = datetime.datetime.now(tz=None)
        res = POOL.map(self._evaluate_dna_mp,dna_series)
        scores = []
        for result in res:
            self.reports['training'][self.serialize_dna(result['DNA'])] = {
                 "reports":result['reports'],
                 "score":result['score']
            }
            scores.append(result['score'])
        v = np.array(scores)
        print("")
        return v

    def _evaluate_dna_mp(self, DNA):
        score, reports = self._evaluate_dna_sp(DNA=DNA, datasource="training")
        with processed_DNA.get_lock():
            # pbar = progressbar.ProgressBar(max_value=pbar_size)
            processed_DNA.value+=1
            # pbar.update(processed_DNA.value)
            # calculate time
            time_elapsed = datetime.datetime.now(tz=None) - start_ts
            progress = processed_DNA.value/pbar_size
            time_eta = (time_elapsed/progress) * (1-progress)
            bar_width = 25
            print("\rLearning Progress: {:>5.1f}% ({:03d}/{:03d}) \t[{}{}]\t Elapsed Time: {}\t ETA: {}".format(
            round(progress*100,2), processed_DNA.value,pbar_size,
            "#"*int(progress*bar_width),"."*(bar_width-int(progress*bar_width)),
            str(time_elapsed).split('.')[0], str(time_eta).split('.')[0]),end="")
        return {
            "DNA": DNA,
            "score": score,
            "reports": pd.DataFrame(reports)
        }

    def _evaluate_dna_sp(self,DNA,datasource):
        if datasource == 'training' or datasource is None:
            datasource = 'training'
            datasets = self.training_sets
        elif datasource=='validation':
            datasets = self.validation_sets

        scores,reports = [],[]
        for dataset in datasets:
            if len(dataset)==0: return None
            mystg = self.strategy(DNA)
            symbol = dataset.iloc[0]['symbol']
            report = mystg.backtest(symbol, dataset)
            score = self._loss_function(report)
            scores.append(score)
            reports.append(report)
            del mystg
        score = round(np.mean(scores),4)
        return score, reports

    def _evaluate_dna_core(self, data):
        DNA, dataset = data[0],data[1]
        if len(dataset)==0: return None
        mystg = self.strategy(DNA)
        symbol = dataset.iloc[0]['symbol']
        report = mystg.backtest(symbol, dataset)
        del mystg
        return report

    def _loss_function(self, report):
        score = report['sess_rate'] * report['win_r'] * report['pb_diff'] * report['wl_rate'] / (report['cont_errs']+1)
        return score

    def evaluate_dna(self, DNA, datasource=None):
        if datasource == 'training' or datasource is None:
            datasource = 'training'
            datasets = self.training_sets
        elif datasource=='validation':
            datasets = self.validation_sets

        pool = mp.Pool(min(MAX_SUB_PROCESSES, len(datasets)))
        res = pool.map(self._evaluate_dna_core, zip(itertools.repeat(DNA), datasets))
        scores = []
        for report in res:
            if report is None: continue
            score = self._loss_function(report)
            scores.append(score)

        score = round(np.mean(scores),4)
        self.reports[datasource][self.serialize_dna(DNA)] = {
             "reports":pd.DataFrame(res),
             "score":score
        }
        pool.close()
        return score

    def print_report(self):
        best_dna = self.pop[-1]
        width=100
        columns=['cont_errs','sessions','win_r','wl_rate','profit','pb_diff','days/sess']
        rows=['mean']

        # print training result
        if self.serialize_dna(best_dna) in self.reports['training']:
            training_result = self.reports['training'][self.serialize_dna(best_dna)]
            training_score  = training_result['score']
            print("="*width)
            print("Training: {}".format(training_score))
            print(np.round(training_result['reports'],3))
            print("-"*width)
            print(np.round(training_result['reports'][columns].describe(),3).loc[rows])
            print("="*width)

        # print validation result
        if self.serialize_dna(best_dna) in self.reports['validation']:
            validation_result = self.reports['validation'][self.serialize_dna(best_dna)]
            validation_score  = validation_result['score']
            print("\n")
            print("Validation: {}".format(validation_score) )
            print(np.round(validation_result['reports'],3))
            print("-"*width)
            print(np.round(validation_result['reports'][columns].describe(),3).loc[rows])
            print("="*width)
            print("\n")

        return

    def serialize_dna(self,dna):
        return hashlib.md5(str(list(dna)).encode('utf-8')).hexdigest()


    def reset_reports(self):
        self.reports = {"training":{}, "validation":{}}
        return

    def evolve(self, training_sets, validation_sets):
        global POOL
        processed_DNA = mp.Value('i', 0)
        POOL = mp.Pool(min(MAX_MAIN_PROCESSES,mp.cpu_count()),initializer=_init_globals, initargs=(POP_SIZE+NEW_KIDS,processed_DNA))

        self.reset_reports()
        self.training_sets = training_sets
        self.validation_sets = validation_sets

        # 主要进化逻辑
        self.kill_bad(self.make_kids())

        best_dna = self.pop[-1]
        print('Validating...',end="")
        validation_score = self.evaluate_dna(DNA=best_dna, datasource="validation")
        validation_result = self.reports['validation'][self.serialize_dna(best_dna)]
        training_score  = self.reports['training'][self.serialize_dna(best_dna)]['score']
        training_result = self.reports['training'][self.serialize_dna(best_dna)]
        print("[DONE]")
        result = {
            "training": training_result,
            "validation": validation_result,
        }

        if self.should_save_knowledge(result):
            self.latest_best_dna     = best_dna
            self.old_training_score  = training_score
            self.old_validation_score= validation_score
            self.save()
        POOL.close()
        return result

    def dump_dna(self):
        best_dna = self.pop[-1]
        mystg = self.strategy(best_dna)
        return mystg.dump_dna()

    def should_save_knowledge(self,result):
        if self.latest_best_dna is None: return True
        decision = False
        if self.old_training_score is None:
            self.old_training_score = self.evaluate_dna(DNA=self.latest_best_dna,datasource="training")
        if self.old_training_score is None:
            self.old_validation_score = self.evaluate_dna(DNA=self.latest_best_dna,datasource="validation")

        if result['training']['score'] > self.old_training_score:
           # if result['validation_score'] >= self.old_validation_score:
           decision = True
        return decision

    def load(self):
        self.latest_best_dna = None
        if os.path.isfile(self.settings_filename):
            with open(self.settings_filename) as json_file:
                data = json.load(json_file)
                self.latest_best_dna = np.array(data['learning']['latest_best_dna'])
                self.pop = np.array(data['learning']['pop'])
        return

    def save(self):
        print('Saving knowledge ...', end="")
        self.pop = np.round(self.pop,4)
        data = { "learning":{
                    "latest_best_dna":self.latest_best_dna.tolist(),
                    "pop":self.pop.tolist()
                  }}
        with open(self.settings_filename, 'w') as outfile:
            json.dump(data, outfile, indent=2)
        print("[DONE]")
        return
