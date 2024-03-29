import sys
import time
import networkx as nx
from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.sql import functions
from graphframes import *
from copy import deepcopy

sc=SparkContext("local", "degree.py")
sqlContext = SQLContext(sc)

def articulations(g, usegraphframe=False):
	#articulations list	
	artList=[]
	
	# Get the starting count of connected components
	# YOUR CODE HERE
	numConnected = g.connectedComponents().groupby('component').count().count()

	# Default version sparkifies the connected components process 
	# and serializes node iteration.
	if usegraphframe:
		# Get vertex list for serial iteration
		# YOUR CODE HERE
		vertexList = g.vertices.map(lambda x: x.id).collect()

		# For each vertex, generate a new graphframe missing that vertex
		# and calculate connected component count. Then append count to
		# the output
		# YOUR CODE HERE

		for vertex in vertexList:
			
			newGraph=GraphFrame(g.vertices.filter("id !=" + str(cId)),g.edges)
			newNumConnected=newGraph.connectedComponents.groupby(lambda x: x.component).count()
			
			if newNumConnected>numConnected:
				artList.append((vertex.id, 1))
			else:
				artList.append((vertex.id, 0))

		artDF = sqlContext.createDataFrame(art,["id", "articulation"])

		
		
	# Non-default version sparkifies node iteration and uses networkx 
	# for connected components count.
	else:
        	# YOUR CODE HERE
		#Convert graphframe to nx graph
		nxg=nx.Graph()
		vertexList = g.vertices.map(lambda x: str(x.id)).collect()
		nxg.add_nodes_from(vertexList)
		nxg.add_edges_from(g.edges.map(lambda x: (x[0], x[1])).collect())

		numConnected=nx.number_connected_components(nxg)

		
		for vertex in vertexList:
			
			newnxg=deepcopy(nxg)
			newnxg.remove_node(vertex)
			newNumConnected=nx.number_connected_components(newnxg)
			
			if newNumConnected>numConnected:
				artList.append((vertex, 1))
			else:
				artList.append((vertex, 0))

		artDF = sqlContext.createDataFrame(artList,["id", "articulation"]) 

	return artDF

	
		

filename = sys.argv[1]
lines = sc.textFile(filename)

pairs = lines.map(lambda s: s.split(","))
e = sqlContext.createDataFrame(pairs,['src','dst'])
e = e.unionAll(e.selectExpr('src as dst','dst as src')).distinct() # Ensure undirectedness 	

# Extract all endpoints from input file and make a single column frame.
v = e.selectExpr('src as id').unionAll(e.selectExpr('dst as id')).distinct()	

# Create graphframe from the vertices and edges.
g = GraphFrame(v,e)





#Runtime approximately 5 minutes
print("---------------------------")
print("Processing graph using Spark iteration over nodes and serial (networkx) connectedness calculations")
init = time.time()
df = articulations(g, False)
print("Execution time: %s seconds" % (time.time() - init))
print("Articulation points:")
df1 = df.filter('articulation = 1')
df1.show(truncate=False)
df1.toPandas().to_csv('articulations_out.csv')
print("---------------------------")

#Runtime for below is more than 2 hours
#print("Processing graph using serial iteration over nodes and GraphFrame connectedness calculations")
#init = time.time()
#df = articulations(g, True)
#print("Execution time: %s seconds" % (time.time() - init))
#print("Articulation points:")
#df.filter('articulation = 1').show(truncate=False)
