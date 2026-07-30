import json
from seaborn import cm
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from sklearn.metrics import f1_score


RESULTS_PATH = "test_results/corpora_validation/validation_results.json"
IN_SCOPE_LANGS = ["ami", "tay", "bnn", "pwn", "pyu", "dru", "trv"]

def read_corpora_validation_results(results_file):
    """
    Reads the corpora validation results from a JSON file and returns a dictionary of the results.
    """
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    return results

def cm_from_results(results, save=True):
    """
    Constructs a confusion matrix from the validation results.
    """
    # Initialize confusion matrix
    y_true = []
    y_pred = []
    for result in results:
        if "predicted_language" not in result:
            continue
        true_lang = result['language']
        predicted_lang = result['predicted_language']
        if true_lang in IN_SCOPE_LANGS and predicted_lang in IN_SCOPE_LANGS:
            y_true.append(true_lang)
            y_pred.append(predicted_lang)
    
    cm = confusion_matrix(y_true, y_pred, labels=IN_SCOPE_LANGS)
    if save:
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=IN_SCOPE_LANGS)
        disp.plot(cmap=plt.cm.Blues)    
        plt.savefig("test_results/corpora_validation/confusion_matrix.png")
        plt.close()
        
    return cm

def f1_scores_from_cm(cm):
    """
    Computes the F1 scores for each class from the confusion matrix.
    """
    y_true = []
    y_pred = []
    for i, true_label in enumerate(IN_SCOPE_LANGS):
        for j, pred_label in enumerate(IN_SCOPE_LANGS):
            y_true.extend([true_label] * cm[i, j])
            y_pred.extend([pred_label] * cm[i, j])
    f1_scores = f1_score(y_true, y_pred, labels=IN_SCOPE_LANGS, average=None)
    return dict(zip(IN_SCOPE_LANGS, f1_scores))


def main():
    # Read the corpora validation results
    results = read_corpora_validation_results(RESULTS_PATH)

    # Construct the confusion matrix
    cm = cm_from_results(results, save=False)
    f1_scores = f1_scores_from_cm(cm)
    print(f1_scores)
    return

if __name__ == "__main__":
    main()