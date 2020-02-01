import os, sys
import numpy as np
import pandas as pd
import progressbar

from .strategy import strategy as stg

POP_SIZE = 10
MAX_POP_SIZE = 20
NEW_KIDS = 60
DNA_LEN = 26
MUT_STRENGTH = 0.05

class learn(object):
    def __init__(self):
        self.settings_filename = os.path.join('data','settings','cfg_.json')
        self.reset()
        self.load()
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
        v = np.zeros(len(dna_series))
        bar = progressbar.ProgressBar(max_value=len(dna_series))
        for i in range(len(dna_series)):
            bar.update(i+1)
            score = self.evaluate_dna(dna_series[i])
            v[i]=score
        return v

    def evaluate_dna(self,DNA):
        mystg = stg(DNA)
        scores = []
        for training_set in self.training_sets:
            if len(training_set)==0: continue
            symbol = training_set.iloc[0]['symbol']
            report = mystg.backtest(symbol, training_set)
            scores.append(report['profit'])
        score = np.mean(scores)
        del mystg
        return score

    def evolve(self,training_sets, validation_sets):
        self.training_sets = training_sets
        self.validation_sets = training_sets
        self.kill_bad(self.make_kids())
        return

    def should_save_knowledge(self,result):
        return

    def save_knowledge(self):
        return

    def load(self):
        if os.path.isfile(self.settings_filename):
            with open(self.settings_filename) as json_file:
                data = json.load(json_file)
                self.latest_best_settings = data['learning']['latest_best_settings']
                self.pop = np.array(data['learning']['pop'])
                self.knowledge_base = data['knowledge_base']
                print("Knowledge base loaded:  {} items".format(len(self.knowledge_base.keys())))
        return

    def save(self):
        self.pop = np.round(self.pop,2)
        data = { "learning":{
                    "latest_best_settings":self.latest_best_settings,
                    "pop":self.pop.tolist()
                  },
                  "knowledge_base":self.knowledge_base,
                  }
        with open(self.settings_filename, 'w') as outfile:
            json.dump(data, outfile, indent=2)
        return
