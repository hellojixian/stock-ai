'''
风险控制模块的机器学习逻辑
先计算基线的分数，然后比较每个动态DNA组合的差异
'''
from base_rc import BaseRiskControl as strategy

class RiskControlLearner(object):
    def __init__(self):
        super().__init__()
        self.strategy = strategy
        self.settings_filename = os.path.join('data','knowledgebase','{}-settings.json'.format(strategy.NAME))
        self.reset()
        self.load()
        return

    def reset(self):
        return

    def evolve(self, training_sets, validation_sets):
        return

    def serialize_dna(self,dna):
        return hashlib.md5(str(list(dna)).encode('utf-8')).hexdigest()


    def reset_reports(self):
        self.reports = {"training":{}, "validation":{}}
        return

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
