#!/usr/bin/env python3
import pandas as pd
import numpy as np
import argparse
import multiprocessing as mp
from lib.datasource import DataSource as ds
from lib.feature_extract import featureExtractor as fe
from lib.backtest import backtest as bt
from lib.strategy import strategy as stg
from lib.learn import learn as ln

if __name__ == "__main__":
    mp.freeze_support()

    parser = argparse.ArgumentParser(description='Machine Learning.')
    parser.add_argument('--batch-size',
                        default=100, type=int,
                        help='how many batch of samples for learning')

    parser.add_argument('--skip-batch',
                        default=0, type=int,
                        help='skip first N of batch')

    parser.add_argument('--step-size',
                        default=30, type=int,
                        help='how many generations for each batch of learning')

    parser.add_argument('--training-set-size',
                        default=10, type=int,
                        help='how many data samples for each batch of learning')

    parser.add_argument('--early_stop',
                        default=3, type=int,
                        help='Stop learning if N batch of improving the result')

    args = vars(parser.parse_args())

    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)


    np.random.seed(0)
    securities = ds.loadSecuirtyList();

    for i in range(args['batch_size']):
        #skip batch logic
        if i < args['skip_batch']: continue

        print("Learning batch :{}".format(i))

        print("Generating training sets:\t",end="")
        # prepare datasets
        training_sets = []
        while len(training_sets)<args['training_set_size']:
            sample = securities.sample(1).iloc[0]
            symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date
            dataset = ds.loadFeaturedData(symbol, start_date, end_date)
            if dataset.shape[0]>0: training_sets.append(dataset)
        print("[DONE]")

        print("Generating validation sets:\t",end="")
        validation_sets = []
        while len(validation_sets)<args['training_set_size']:
            sample = securities.sample(1).iloc[0]
            symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date
            dataset = ds.loadFeaturedData(symbol, start_date, end_date)
            if dataset.shape[0]>0: validation_sets.append(dataset)
        print("[DONE]")

        ml = ln()
        last_score = 0
        stop_improving_counter = 0
        for _ in range(args['step_size']):
            print("Batch :{}\t GA Learning step: {}".format(i,_))
            report = ml.evolve(training_sets=training_sets, validation_sets=validation_sets)

            # early stop logic
            if report['validation_score'] == last_score:
                stop_improving_counter+=1
                print("Not improving result: {}".format(stop_improving_counter))
            if stop_improving_counter>=args['eraly_stop']:
                print("Early stop learning")
                break
            last_score = report['validation_score']

            print(report)
        ml.save()
        del ml

        print("-"*100)
        print("\n")
