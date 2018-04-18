import os
import warnings
warnings.filterwarnings("ignore")

from citrination_client import CitrinationClient
from xrsdkit.models.classifiers import Classifiers
from xrsdkit.models.regressors import Regressors

from xrsdkit.tools.citrination_tools import get_data_from_Citrination

p = os.path.abspath(__file__)
d = os.path.dirname(os.path.dirname(os.path.dirname(p)))

api_key_file = os.path.join(d, 'api_key.txt')
if not os.path.exists(api_key_file):
    print("Citrination api key file did not find")

with open(api_key_file, "r") as g:
    a_key = g.readline().strip()
cl = CitrinationClient(site='https://slac.citrination.com',api_key=a_key)


#data = get_data_from_Citrination(client = cl, dataset_id_list= [21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36])
data = get_data_from_Citrination(client = cl, dataset_id_list= [21,22,23,24,25,26,27,28,29,30,31,32,33])

models_path = os.path.join(d,'xrsdkit','models','modeling_data')

my_classifiers = Classifiers() # we can specify the list of classifiers to train
print("Old accuracies for classifiers:")
my_classifiers.print_accuracies()

results = my_classifiers.train_classification_models(data, hyper_parameters_search = True)
# to train 'guinier_porod_population_count' model only:
#results = my_classifiers.train_classification_models(data, hyper_parameters_search = True, cl_models = ['guinier_porod_population_count'])
print("New accuracies and parameters for classifiers:")
my_classifiers.print_training_results(results)
my_classifiers.save_classification_models(results, models_path)


# regression models:
rg_models = Regressors()
print("Old accuracies for regressors:")
rg_models.print_errors()

results = rg_models.train_regression_models(data, hyper_parameters_search = True)
print("New accuracies and parameters for regressors:")
rg_models.print_training_results(results)
rg_models.save_regression_models(results, models_path)


