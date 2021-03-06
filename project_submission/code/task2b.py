import dbInfo as db
import numpy as np
import svd
import utils
import similarity
#np.set_printoptions(threshold=np.nan)

sim = similarity.getCoactorMatrix()
mat = np.matmul(sim,np.transpose(sim))
svdSem = svd.svdCalc(mat, 3)
allActors = db.getAllActors()
actorNames = db.getAllActorNames()
print("\n\nCoactor-Coactor Similarity Matrix:\n",mat,"\n\nsize of matrix :", mat.shape)
print("\n\nTop 3 Latent Semantics:\n")
for sem in svdSem:
	print("\n\n",utils.rankSem(sem, allActors))
groups = utils.form_groups_semantics(np.transpose(svdSem),actorNames,3)
print("\n\n3 Non overlapping groups:")
for grp in groups.keys():
	print("\n\n",grp, ":", groups[grp])
