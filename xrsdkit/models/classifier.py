import numpy as np
from collections import OrderedDict

from sklearn import linear_model, model_selection
from sklearn.metrics import f1_score, confusion_matrix

from .xrsd_model import XRSDModel

class Classifier(XRSDModel):
    """Class for generating models to classifying material systems."""

    def __init__(self,label,yml_file):
        super(Classifier,self).__init__(label, yml_file)
        self.grid_search_hyperparameters = dict(
            penalty = ['none', 'l2', 'l1', 'elasticnet'], # default: l2
            alpha = [0.00001, 0.0001, 0.001, 0.01, 0.1], # regularisation coef, default 0.0001
            l1_ratio = [0, 0.15, 0.5, 0.85, 1.0] # default 0.15, only valid for elasticnet penalty
            )

    def build_model(self,model_hyperparams={}):
        if all([p in model_hyperparams for p in ['alpha','penalty','l1_ratio']]):
            new_model = linear_model.SGDClassifier(
                    alpha=model_hyperparams['alpha'], 
                    loss='log',
                    penalty=model_hyperparams['penalty'], 
                    l1_ratio=model_hyperparams['l1_ratio'],
                    max_iter=10)
        else:
            new_model = linear_model.SGDClassifier(loss='log', max_iter=10)
        return new_model

    def classify(self, sample_features):
        """Classify the model target for a sample.

        Parameters
        ----------
        sample_features : OrderedDict
            OrderedDict of features with their values,
            similar to output of xrsdkit.tools.profiler.profile_spectrum()

        Returns
        -------
        structure_flags : bool or None
            a boolean inidicating whether or not
            the sample exhibits the structure
            None is reterned for models that was not trained yet
        cert : float or None
            the certainty of the prediction
            None is reterned for models that was not trained yet
        """
        feature_array = np.array(list(sample_features.values())).reshape(1,-1)
        x = self.scaler.transform(feature_array)
        sys_cls = self.model.predict(x)[0]
        cert = max(self.model.predict_proba(x)[0])
        return sys_cls, cert

    def run_cross_validation(self,model,data,features,n_groups_out):
        """
        'f1_macro' used for classifiers as scoring function;
        f1_macro is averaged unweighted f1 calculated by labels.
        Training reports also include mean unweighted accuracies by labels since it is
        more intuitive.
        Unfortunately, sklearn does not provide mean unweighted accuracy by labels
        as a scoring option and it cannot be used for hyperparameters search.
        """
        if n_groups_out:
            cross_val_results = self.cross_validate_by_experiments(model,data,features)
        else:
            cross_val_results = self.cross_validate(model,data,features)
        return cross_val_results


    def cross_validate_by_experiments(self, model, df, features):
        """Test a model by LeaveOneGroupOut cross-validation.

        Parameters
        ----------
        df : pandas.DataFrame
            pandas dataframe of features and labels
            must include the data from at least 3 experiments
        model : sk-learn
            with specific parameters
        features : list of str
            list of features that were used for training.

        Returns
        -------
        test_scores_by_ex : dict
            includes list of all labels,
            number of experiments,list of all experiments, confusion matrix,
            list of labels for which the models were not tested,
            list of labels for which the models were tested,
            F1 score by classes, averaged F1 score weighted and unweighted,
            mean accuracies by classes,
            mean unweighted and weighted by classes accuracy,
            test training split.
        """
        experiments = df.experiment_id.unique()# we have at least 3 experiments
        all_classes = df[self.target].unique().tolist()
        test_scores_by_ex = {}
        test_scores_by_classes = dict.fromkeys(all_classes)
        for k,v in test_scores_by_classes.items():
            test_scores_by_classes[k] = []
        scores = []
        true_labels = []
        pred_labels = []
        acc_weighted_by_classes = []
        for i in range(len(experiments)):
            tr = df[(df['experiment_id'] != experiments[i])]
            if len(tr[self.target].unique()) < 2:
                continue
            test = df[(df['experiment_id'] == experiments[i])]
            # remove from the test set the samples of the classes
            # that do not exists in the training set:
            cl_in_training_set = tr[self.target].unique()
            test = test[(test[self.target].isin(cl_in_training_set))]

            model.fit(tr[features], tr[self.target])
            y_pred = model.predict(test[features])

            pred_labels.extend(y_pred)
            true_labels.extend(test[self.target])

            labels_from_test = test[self.target].value_counts().keys().tolist()

            cmat = confusion_matrix(test[self.target], y_pred, labels_from_test)

            # for each class we devided the number of right predictions
            # by the total number of samples for this class at test set:
            accuracies_by_classes = cmat.diagonal()/test[self.target].value_counts().tolist()
            acc_weighted_by_classes.append(sum(cmat.diagonal())/test.shape[0])

            average_acc_for_this_exp = sum(accuracies_by_classes)/len(accuracies_by_classes)
            scores.append(average_acc_for_this_exp)

            for k in range(len(labels_from_test)):
                test_scores_by_classes[labels_from_test[k]].append(accuracies_by_classes[k])

        # we may not be able to test for all classes
        # (if samples of a class are included into only one experiment)
        not_tested_classes = []
        tested_sys_classes = []
        score_by_cl = []
        for k, v in test_scores_by_classes.items():
            if test_scores_by_classes[k] == []:
                not_tested_classes.append(k)
            else:
                tested_sys_classes.append(k)
                av = sum(test_scores_by_classes[k])/len(test_scores_by_classes[k])
                test_scores_by_classes[k] = av
                score_by_cl.append(av)

        result = dict(all_classes = all_classes,
                      number_of_experiments = len(experiments),
                      experiments = str(df.experiment_id.unique()),
                      confusion_matrix = str(confusion_matrix(true_labels, pred_labels, all_classes)),
                      model_was_NOT_tested_for = not_tested_classes,
                      model_was_tested_for = tested_sys_classes,
                      F1_score_by_classes = f1_score(true_labels, pred_labels,
                                    labels=tested_sys_classes, average=None).tolist(),
                      F1_score_averaged_not_weighted = f1_score(true_labels,
                                        pred_labels, labels=tested_sys_classes, average='macro'),
                      F1_score_averaged_weighted = f1_score(true_labels,
                                        pred_labels, labels=tested_sys_classes, average='weighted'),
                      mean_accuracies_by_classes = test_scores_by_classes,
                      mean_not_weighted_accuracy = sum(score_by_cl)/len(score_by_cl),
                      mean_weighted_by_classes_accuracy = sum(acc_weighted_by_classes)/len(acc_weighted_by_classes),
                      test_training_split = "by experiments")
        return result


    def cross_validate(self,model,df,features):
        # some of metrics have None since they cannot be calculated using cross_val_score from sklearn
        results = dict(all_classes = df[self.target].unique().tolist(),
                       number_of_experiments = len(df.experiment_id.unique()),
                       experiments = str(df.experiment_id.unique()),
                       confusion_matrix = None,
                       model_was_NOT_tested_for = None,
                       model_was_tested_for = df[self.target].unique().tolist(), #same as all_classes
                       F1_score_by_classes = [],
                       mean_accuracies_by_classes = None,
                       mean_not_weighted_accuracy= None)

        if min(df[self.target].value_counts()) > 2:
            results['mean_weighted_by_classes_accuracy'] = model_selection.cross_val_score(model,df[features],
                                                        df[self.target],cv=3, scoring='accuracy'),
            results['F1_score_averaged_not_weighted'] = model_selection.cross_val_score(model,df[features],
                                                        df[self.target],cv=3, scoring='f1_macro')
            results['F1_score_averaged_weighted'] = model_selection.cross_val_score(model,df[features],
                                                        df[self.target],cv=3, scoring='f1_weighted')
            results['mean_weighted_by_classes_accuracy'] = model_selection.cross_val_score(model,df[features],
                                                        df[self.target],cv=3, scoring='accuracy')
            results['test_training_split'] = "random 3 folders crossvalidation split"
        else:
            results['mean_weighted_by_classes_accuracy'] = None
            results['F1_score_averaged_not_weighted'] = None
            results['F1_score_averaged_weighted'] = None
            results['mean_weighted_by_classes_accuracy'] = None
            results['test_training_split'] = "The model was not crossvalidated since we have" \
                                             " less than 3 samples for some labels "
        return results

    def hyperparameters_search(self,transformed_data, data_labels, group_by=None, n_leave_out=None, scoring='f1_macro'):
        """Grid search for optimal alpha, penalty, and l1 ratio hyperparameters.
        This invokess the method from the base class with a different scoring argument.

        Returns
        -------
        params : dict
            dictionary of the parameters to get the best f1 score.
        """
        params = super(Classifier,self).hyperparameters_search(
        transformed_data,data_labels,group_by,n_leave_out,scoring)
        return  params

    def print_number_of_exp(self):
        return str(self.cross_valid_results['number_of_experiments'])

    def print_labels(self, all=True):
        if all:
            labels = self.cross_valid_results['all_classes']
        else:
            labels = self.cross_valid_results['model_was_NOT_tested_for']
        if labels:
            result = ''
            for l in labels:
                result += l
                result += '\n'
            return result
        else:
            return "The model was tested for all labels"

    def print_confusion_matrix(self):
        if self.cross_valid_results['confusion_matrix']:
            result = ''
            matrix = self.cross_valid_results['confusion_matrix'].split('\n')
            #for i in range(len(self.cross_valid_results['model_was_tested_for'])):
            for i in range(len(self.cross_valid_results['all_classes'])):
                result += (matrix[i] + "  " +
                        #self.cross_valid_results['model_was_tested_for'][i] + '\n')
                        self.cross_valid_results['all_classes'][i] + '\n')
            return result
        else:
            return "Comfusion matrix was not created"

    def print_F1_scores(self):
        result = ''
        for i in range(len(self.cross_valid_results['F1_score_by_classes'])):
            result += (self.cross_valid_results['model_was_tested_for'][i] +
                       " : " + str(self.cross_valid_results['F1_score_by_classes'][i]) + '\n')
        return result

    def print_accuracies(self):
        if self.cross_valid_results['mean_accuracies_by_classes']:
            result = ''
            for k,v in self.cross_valid_results['mean_accuracies_by_classes'].items():
                result += (k + " : " + str(v) + '\n')
            return result
        else:
            return "Mean accuracies by classes were not calculated"

    def average_F1(self,weighted=False):
        if weighted:
            return str(self.cross_valid_results['F1_score_averaged_weighted'])
        else:
            return str(self.cross_valid_results['F1_score_averaged_not_weighted'])

    def average_accuracy(self,weighted=False):
        if weighted:
            return str(self.cross_valid_results['mean_weighted_by_classes_accuracy'])
        else:
            if self.cross_valid_results['mean_not_weighted_accuracy']:
                return str(self.cross_valid_results['mean_not_weighted_accuracy'])
            else:
                return "Mean not weighted accuracy was not calculated"

    def print_CV_report(self):
        """Return a string describing the model's cross-validation metrics.

        Returns
        -------
        CV_report : str
            string with formated results of cross validatin.
        """
        CV_report = 'Cross validation results for {} Classifier\n\n'.format(self.target) + \
            'Data from {} experiments was used\n\n'.format(self.print_number_of_exp()) + \
            'All labels : \n' + self.print_labels()+'\n\n'+ \
            'model was NOT tested for :' '\n'+ self.print_labels(False) +'\n\n'+ \
            'Confusion matrix:\n' + \
            'if the model was not tested for some labels, the corresponding rows will have all zeros\n' + \
            self.print_confusion_matrix()+'\n\n' + \
            'F1 scores by label:\n' + \
            self.print_F1_scores() + '\n'\
            'Label-averaged unweighted F1 score: {}\n\n'.format(self.average_F1(False)) + \
            'Label-averaged weighted F1 score: {}\n\n'.format(self.average_F1(True)) + \
            'Accuracies by label:\n' + \
            self.print_accuracies() + '\n'+\
            'Label-averaged unweighted accuracy: {}\n\n'.format(self.average_accuracy(False)) + \
            'Label-averaged weighted accuracy: {}\n'.format(self.average_accuracy(True))+ '\n\n'+\
            'NOTE: Weighted metrics are weighted by class size'
        return CV_report

