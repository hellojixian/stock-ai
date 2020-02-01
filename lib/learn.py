import os, sys, json
import numpy as np
import pandas as pd
import progressbar
import multiprocessing as mp

from .strategy import strategy as stg

POP_SIZE = 40 #40
MAX_POP_SIZE = 20
NEW_KIDS = 60 #60
DNA_LEN = 26
MUT_STRENGTH = 0.03

POOL = None

def _init_globals(pbar_size):
    global pbar,processed_DNA
    pbar = progressbar.ProgressBar(max_value=pbar_size)
    processed_DNA   = mp.Value('i', 0)
    return

class learn(object):
    def __init__(self):
        self.settings_filename = os.path.join('data','knowledgebase','settings.json')
        self.reset()
        self.load()
        self.init_mp_pool()
        return

    def __del__(self):
        global POOL
        POOL.close()
        return

    def init_mp_pool(self):
        global POOL
        POOL = mp.Pool(mp.cpu_count(),initializer=_init_globals, initargs=(POP_SIZE+NEW_KIDS,))
        return

    def reset(self):
        self.pop = []
        self.pop_size = POP_SIZE
        self.n_kids = NEW_KIDS
        self.mut_strength = MUT_STRENGTH
        if len(self.pop)==0: self.pop = self.gen_DNAset()
        return

    def gen_DNAset(self):
        dna_list = []
        for i in range(self.pop_size):
            dna_list.append(np.random.rand(DNA_LEN)*2)
        dna_list = np.array(dna_list)
        return dna_list

    def make_kids(self):
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
                kid[i] = np.clip(v, -1, 2.5)
        return kids

    def kill_bad(self, kids):
        self.pop = np.vstack((self.pop, kids))
        fitness = self.get_fitness(self.pop)            # calculate global fitness
        idx = np.arange(self.pop.shape[0])
        good_idx = idx[fitness.argsort()][-self.pop_size:]   # selected by fitness ranking (not value)
        self.pop = self.pop[good_idx]
        return

    def get_fitness(self, dna_series):
        global POOL
        with processed_DNA.get_lock():
            processed_DNA.value = 0
            pbar.max_value = len(dna_series)
            pbar.update(0)

        res = POOL.map(self._evaluate_dna_mp,dna_series)
        v = np.array(res)

        return v

    def _evaluate_dna_mp(self, DNA):
        datasets = self.training_sets
        result = self.evaluate_dna(DNA=DNA, datasets=datasets)
        with processed_DNA.get_lock():
            processed_DNA.value+=1
            pbar.update(processed_DNA.value)
        return result

    def evaluate_dna(self, DNA, datasets=None):
        if datasets is None: datasets = self.training_sets
        scores = []
        for training_set in datasets:
            mystg = stg(DNA)
            if len(training_set)==0: continue
            symbol = training_set.iloc[0]['symbol']
            report = mystg.backtest(symbol, training_set)
            scores.append(report['profit'])
            del mystg
        score = round(np.mean(scores),4)
        return score

    def evolve(self, training_sets, validation_sets):
        self.training_sets = training_sets
        self.validation_sets = validation_sets
        self.kill_bad(self.make_kids())

        best_dna = self.pop[-1]
        result = {
            "training_score": self.evaluate_dna(DNA=best_dna, datasets=self.training_sets),
            "validation_score": self.evaluate_dna(DNA=best_dna, datasets=self.validation_sets)
        }
        if self.should_save_knowledge(result):
            self.latest_best_dna=best_dna
            self.save()

        return result

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
                  }
                }
        with open(self.settings_filename, 'w') as outfile:
            json.dump(data, outfile, indent=2)
        print("[DONE]")
        return
