import numpy as np
from sklearn.metrics import roc_curve, auc, confusion_matrix

def eer_and_auc(y_true, y_scores):
    """
    y_true: np.array of {0,1}  (1=bonafide)
    y_scores: np.array of probabilities for class 1
    """
    fpr, tpr, _ = roc_curve(y_true, y_scores, pos_label=1)
    fnr = 1 - tpr
    idx = np.nanargmin(np.abs(fnr - fpr))
    eer = (fnr[idx] + fpr[idx]) / 2.0
    roc_auc = auc(fpr, tpr)
    return float(eer), float(roc_auc)

def confusion(y_true, y_pred):
    # returns TN, FP, FN, TP
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0,1]).ravel()
    return tn, fp, fn, tp
