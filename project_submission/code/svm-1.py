import numpy as np
import csv
import random
import math
import dbInfo as di
import tfIdfCalc as idf
import operator
import numpy

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils import check_random_state
from sklearn.preprocessing import LabelEncoder

def loadDataset(filename, trainingSet=[] , testSet=[]):
    
    with open(filename, 'r') as csvfile:
        lines = csv.reader(csvfile)
        dataset = list(lines)
    labels=['' for i in range(len(dataset))]
    movies = di.getAllMovies()
    tagIds = di.getAllTags()
    allTagLen = len(tagIds)
    dataset_copy = [['' for i in range(allTagLen)] for j in range(len(dataset))]
    #dataset_copy = numpy.zeros((len(movies),allTagLen+1))
    #dataset_copy = [[0 for i in range(allTagLen+1)] for j in range(len(movies))]
    idfMovArr = idf.idfMovieTag()
    #print(idfMovArr)
    for i in range(len(dataset)):
        idfVect = idf.tfIdfMovieTag(dataset[i][0], idfMovArr)
        for j in range(len(idfVect)):
            dataset_copy[i][j] = idfVect[j]
        #dataset_copy[i][allTagLen]=dataset[i][1]
        labels[i]=dataset[i][1]
        trainingSet.append(dataset_copy[i])
    train = [0 for i in range(len(dataset))]

    target=['' for i in range(len(movies))]
    for i in range(len(dataset)):
        train[i] = int(dataset[i][0])
    k=0
    test=[]
    label = ['0', '1']
    testset_copy = [['' for i in range(allTagLen)] for j in range(len(movies))]
    for i in range(len(movies)):
            if(int(movies[i][0]) in train):
                pass
            else:
                test.append(movies[i][0])
                idfVect1 = idf.tfIdfMovieTag(movies[i][0], idfMovArr)
                for j in range(len(idfVect1)):
                    testset_copy[k][j] = idfVect1[j]
                #testset_copy[k][allTagLen]=di.getMovieGenre(movies[i][0])[0]
                #testset_copy[k][allTagLen]=random.choice(labels)
                target[k]=random.choice(label)
                testSet.append(testset_copy[k])
                k=k+1
    #print("train data =",trainingSet)
    #print("\n\n test data =",testSet)
    return trainingSet,testSet,labels,target,test

def projection_simplex(v, z=1):
    """
    Projection onto the simplex:
        w^* = argmin_w 0.5 ||w-v||^2 s.t. \sum_i w_i = z, w_i >= 0
    """
    n_features = v.shape[0]
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u) - z
    ind = np.arange(n_features) + 1
    cond = u - cssv / ind > 0
    rho = ind[cond][-1]
    theta = cssv[cond][-1] / float(rho)
    w = np.maximum(v - theta, 0)
    return w


class MulticlassSVM(BaseEstimator, ClassifierMixin):

    def __init__(self, C=1, max_iter=50, tol=0.05,
                 random_state=None, verbose=0):
        self.C = C
        self.max_iter = max_iter
        self.tol = tol,
        self.random_state = random_state
        self.verbose = verbose

    def _partial_gradient(self, X, y, i):
        # Partial gradient for the ith sample.
        g = np.dot(X[i], self.coef_.T) + 1
        g[y[i]] -= 1
        return g

    def _violation(self, g, y, i):
        # Optimality violation for the ith sample.
        smallest = np.inf
        for k in range(g.shape[0]):
            if k == y[i] and self.dual_coef_[k, i] >= self.C:
                continue
            elif k != y[i] and self.dual_coef_[k, i] >= 0:
                continue

            smallest = min(smallest, g[k])

        return g.max() - smallest

    def _solve_subproblem(self, g, y, norms, i):
        # Prepare inputs to the projection.
        Ci = np.zeros(g.shape[0])
        Ci[y[i]] = self.C
        beta_hat = norms[i] * (Ci - self.dual_coef_[:, i]) + g / norms[i]
        z = self.C * norms[i]

        # Compute projection onto the simplex.
        beta = projection_simplex(beta_hat, z)

        return Ci - self.dual_coef_[:, i] - beta / norms[i]

    def fit(self, X, y):
        n_samples, n_features = X.shape

        # Normalize labels.
        self._label_encoder = LabelEncoder()
        y = self._label_encoder.fit_transform(y)

        # Initialize primal and dual coefficients.
        n_classes = len(self._label_encoder.classes_)
        self.dual_coef_ = np.zeros((n_classes, n_samples), dtype=np.float64)
        self.coef_ = np.zeros((n_classes, n_features))

        # Pre-compute norms.
        norms = np.sqrt(np.sum(X ** 2, axis=1))

        # Shuffle sample indices.
        rs = check_random_state(self.random_state)
        ind = np.arange(n_samples)
        rs.shuffle(ind)

        violation_init = None
        for it in range(self.max_iter):
            violation_sum = 0

            for ii in range(n_samples):
                i = ind[ii]

                # All-zero samples can be safely ignored.
                if norms[i] == 0:
                    continue

                g = self._partial_gradient(X, y, i)
                v = self._violation(g, y, i)
                violation_sum += v

                if v < 1e-12:
                    continue

                # Solve subproblem for the ith sample.
                delta = self._solve_subproblem(g, y, norms, i)

                # Update primal and dual coefficients.
                self.coef_ += (delta * X[i][:, np.newaxis]).T
                self.dual_coef_[:, i] += delta

            if it == 0:
                violation_init = violation_sum

            vratio = violation_sum / violation_init
            

        return self

    def predict(self, X):
        decision = np.dot(X, self.coef_.T)
        pred = decision.argmax(axis=1)
        return self._label_encoder.inverse_transform(pred)


if __name__ == '__main__':
	from sklearn.datasets import load_iris

	trainingSet=[]
	testSet=[]
	trainingSet, testSet,labels,target,test = loadDataset('foo1.csv',trainingSet, testSet)
	#print(test)
	clf = MulticlassSVM(C=0.1, tol=0.01, max_iter=100, random_state=0, verbose=1)
	clf.fit(np.array(trainingSet), np.array(labels))
	resArr = clf.predict(testSet)
	csvArr = [['' for i in range(3)] for j in range(len(resArr)+1)]
	csvArr[0][0] = 'movie_id'
	csvArr[0][1] = 'movie_name'
	csvArr[0][2] = 'class'
	for i in range(len(test)):
		mvName = di.getMovName(test[i])
		print("for movie :",test[i],mvName[0]," > predicted=" ,resArr[i])
		csvArr[i+1][0] = test[i]
		csvArr[i+1][1] = mvName[0]
		csvArr[i+1][2] = resArr[i]
	#print(csvArr)
	np.savetxt('resSVM.csv', csvArr, fmt='%s',delimiter = ',') 