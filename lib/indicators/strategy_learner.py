import os, sys, json
import numpy as np
import pandas as pd
import progressbar
import multiprocessing as mp
import datetime

POP_SIZE = 36 #40
NEW_KIDS = 90 #60
DNA_LEN = 26
MUT_STRENGTH = 0.03
POOL = None
DNA_MIN, DNA_MAX = -5,5

def _init_globals(bar_size, counter):
    global pbar_size,processed_DNA, start_ts
    start_ts = datetime.datetime.now(tz=None)
    pbar_size = bar_size
    processed_DNA  = counter
    return

class StrategyLearner(object):
    """这个英国作为策略的一个学习器"""

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
        v = np.array(res)
        print("")
        return v

    def _evaluate_dna_mp(self, DNA):
        datasets = self.training_sets
        result = self.evaluate_dna(DNA=DNA, datasets=datasets)
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
        return result

    def evaluate_dna(self, DNA, datasets=None):
        if datasets is None: datasets = self.training_sets
        scores = []
        for training_set in datasets:
            mystg = self.strategy(DNA)
            if len(training_set)==0: continue
            symbol = training_set.iloc[0]['symbol']
            report = mystg.backtest(symbol, training_set)
            score = (report['win_rate'] * report['sessions']) / (report['max_continue_errs']+1)
            scores.append(score)
            del mystg
        score = round(np.mean(scores),4)
        return score

    def gen_detailed_report(self, DNA, datasets):
        if datasets is None: datasets = self.training_sets
        scores = []
        for training_set in datasets:
            mystg = self.strategy(DNA)
            if len(training_set)==0: continue
            symbol = training_set.iloc[0]['symbol']
            report = mystg.backtest(symbol, training_set)
            score = report['profit']
            scores.append(score)
            del mystg

        return {
            "profit":{
                "min": np.min(scores),
                "max": np.max(scores),
                "mean": np.mean(scores),
                "median": np.median(scores)
            }
        }


    def evolve(self, training_sets, validation_sets):
        global POOL
        processed_DNA = mp.Value('i', 0)
        POOL = mp.Pool(mp.cpu_count(),initializer=_init_globals, initargs=(POP_SIZE+NEW_KIDS,processed_DNA))

        self.training_sets = training_sets
        self.validation_sets = validation_sets
        self.kill_bad(self.make_kids())

        best_dna = self.pop[-1]
        result = {
            "training_score": self.evaluate_dna(DNA=best_dna, datasets=self.training_sets),
            "validation_score": self.evaluate_dna(DNA=best_dna, datasets=self.validation_sets),
            "report": self.gen_detailed_report(DNA=best_dna, datasets=self.training_sets),
        }
        if self.should_save_knowledge(result):
            self.latest_best_dna=best_dna
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
        old_training_score = self.evaluate_dna(DNA=self.latest_best_dna,
                                               datasets=self.training_sets)
        old_validation_score = self.evaluate_dna(DNA=self.latest_best_dna,
                                               datasets=self.validation_sets)
        if result['training_score'] > old_training_score:
           if result['validation_score'] >= old_validation_score:
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
