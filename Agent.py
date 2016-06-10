# Your Agent for solving Raven's Progressive Matrices. You MUST modify this file.
#
# You may also create and submit new files in addition to modifying this file.
#
# Make sure your file retains methods with the signatures:
# def __init__(self)
# def Solve(self,problem)
#
# These methods will be necessary for the project's main method to run.

# Install Pillow and uncomment this line to access image processing.
#from PIL import Image
#import numpy

class SemNet:
    def __init__(self, figureA, figureB):
        self.transitionEdges = {}
        self.fromSet = NodeSet(figureA)
        self.toSet = NodeSet(figureB)
        self.transitionsFromNodeSet(self.fromSet, self.toSet)

    def addTransitionEdge(self, label, fromNode, toNode):
        edge = Edge(label, toNode)
        fromNode.addEdge(edge)
        if label not in self.transitionEdges:
            self.transitionEdges[label] = 1
        else:
            self.transitionEdges[label] += 1

    def findUnchangedTransitionEdges(self, firstSet, secondSet):
        unchanced = {}
        for nodeName in firstSet.nodes:
            node = firstSet.nodes[nodeName]
            for nodeToCompareName in secondSet.nodes:
                nextNode = secondSet.nodes[nodeToCompareName]
                if node.exactSameAttributes(nextNode):
                    unchanced[nodeToCompareName] = nextNode
                    unchanced[nodeName] = node
                    self.addTransitionEdge("unchanged", node, nextNode)
                elif node.exactSameAttributesExcept("fill", nextNode):
                    unchanced[nodeToCompareName] = nextNode
                    unchanced[nodeName] = node
                    self.addTransitionEdge("shape unchanged", node, nextNode)
        return  unchanced

    def addBasicTransitionEdges(self, fromNode, toNode):
        addedTransition = False
        if fromNode.rotated(toNode):
            self.addTransitionEdge("rotated " + str(fromNode.rotationDifference(toNode)) +" diff", fromNode, toNode)
            addedTransition = True

        if fromNode.fillChanged(toNode):
            self.addTransitionEdge("fill_changed", fromNode, toNode)
            addedTransition = True

        if fromNode.morphed(toNode):
            self.addTransitionEdge("morphed", fromNode, toNode)
            addedTransition = True

        alignment = fromNode.alignmentToNode(toNode)
        if len(alignment) > 0:
            self.addTransitionEdge(alignment, fromNode, toNode)
        return addedTransition

    def transitionsFromNodeSet(self, firstSet, secondSet):
        nodesAdded = self.findUnchangedTransitionEdges(firstSet, secondSet)
        for nodeName in firstSet.nodes:
            if nodeName in nodesAdded:
                continue
            node = firstSet.nodes[nodeName]
            for nodeToCompareName in secondSet.nodes:
                if nodeToCompareName not in nodesAdded:
                    if self.addBasicTransitionEdges(node, secondSet.nodes[nodeToCompareName]):
                        nodesAdded[nodeName] = node
                        nodesAdded[nodeToCompareName] = node
                        break
            if nodeName not in nodesAdded:
                self.addTransitionEdge("deleted", node, node)

    def compare(self, otherSemNet):

        for key in self.transitionEdges:
            if key not in otherSemNet.transitionEdges:
                return False
        return True

    def fromFigure(self, figure):
        nodeSet = NodeSet(figure)
        self.matchObjectsFrom(nodeSet, self.fromSet)
        return nodeSet

    def matchObjectsFrom(self, nodeSet, toNodeSet):
        addedNode = self.findUnchangedTransitionEdges(nodeSet, toNodeSet)
        for nodeName in nodeSet.nodes:
            if nodeName in addedNode:
                continue
            node = nodeSet.nodes[nodeName]
            for matchNodeName in toNodeSet.nodes:
                if nodeName not in addedNode:
                    matchNode = toNodeSet.nodes[matchNodeName]
                    if node.sameObject(matchNode):
                        addedNode[matchNodeName] = matchNode
                        addedNode[nodeName] = node
                        node.addEdges(matchNode.edges)
            if nodeName not in addedNode:
                edge = Edge("unchanged", node)
                node.addEdge(edge)

    def findAnswerFrom(self, possibleAnswers):
        answersToCheck = possibleAnswers.copy()
        for key in answersToCheck.copy():
            if self.transitionEdges != possibleAnswers[key].transitionEdges:
                if key in answersToCheck: del answersToCheck[key]
        return answersToCheck


class Edge:
    def __init__(self, label, node):
        self.label = label
        self.node = node

    def sameEdge(self, otherEdge):
        return self.label == otherEdge.label



class Node:
    def __init__(self, name, object):
        self.name = name
        self.edges = []
        self.attributes = object.attributes

    def sameObject(self, otherNode):
        return self.sameAttribute("size", otherNode) and self.sameAttribute("shape", otherNode)

    def addEdge(self, edge):
        self.edges.append(edge)

    def addEdges(self, node):
        for edge in node:
            self.addEdge(edge)

    def hasEdgeNamed(self, name):
        for edge in self.edges:
            if edge.label == name:
                return True
        return False

    def hasAttributeWithName(self, attributeName):
        return  attributeName in self.attributes

    def sameAttribute(self, attributeName, otherNode):
        if attributeName in self.attributes and attributeName in otherNode.attributes:
            return self.attributes[attributeName] == otherNode.attributes[attributeName]
        return False

    def rotationDifference(self, otherNode):
        diff = 0
        if "angle" in self.attributes and "angle" in otherNode.attributes:
                diff = abs(int(self.attributes["angle"]) - int(otherNode.attributes["angle"]))
        return diff

    def rotated(self, otherNode):
        hasRotated = False
        if self.sameAttribute("shape", otherNode) and self.sameAttribute("size", otherNode):
            hasRotated = self.rotationDifference(otherNode) > 0
        return hasRotated

    def fillChanged(self, otherNode):
        fillChange = False
        if "fill" in self.attributes and "fill" in otherNode.attributes:
            fillChange = self.attributes["fill"] != otherNode.attributes["fill"]
        return fillChange

    def morphed(self, otherNode):
        morphed = False
        if (self.sameAttribute("shape", otherNode) == False or self.sameAttribute("size", otherNode) == False):
            morphed = self.sameRelationshipEdges(otherNode)
        return morphed

    def alignmentToNode(self, otherNode):
        alignment = ""
        if "alignment" in self.attributes and "alignment" in otherNode.attributes:
            alignments = self.attributes["alignment"].split("-")
            alignmentsOfOtherNode = otherNode.attributes["alignment"].split("-")
            index = 0
            while index < len(alignments):
                alignment += ":same:" if alignments[index] == alignmentsOfOtherNode[index] else ":changed:"
                index += 1
        return alignment

    def sameRelationshipEdges(self, otherNode):
        for edge in self.edges:
            if otherNode.hasEdgeNamed(edge.label) == False:
                return False
        return True

    def exactSameAttributesExcept(self, exceptAttribute, otherNode):
        for attribute in self.attributes:
            if attribute != "inside" and attribute != exceptAttribute:
                if self.sameAttribute(attribute, otherNode) == False:
                    return False
        return self.sameRelationshipEdges(otherNode)

    def exactSameAttributes(self, otherNode):
        for attribute in self.attributes:
            if attribute != "inside" and attribute != "above":
                if self.sameAttribute(attribute, otherNode) == False:
                    return False
        return True

    def sameEdges(self, otherNode):
        for edge in self.edges:
            if otherNode.hasEdgeNamed(edge.label) == False:
                return False
        for edge in otherNode.edges:
            if self.hasEdgeNamed(edge.label) == False:
                return False

class NodeSet:
    def __init__(self, figure):
        self.nodes = {}
        self.generateNodesAndRelationshipsFromFigure(figure)

    def findOrCreateNode(self, objectName, object):
        node = None
        if objectName not in self.nodes:
            node = Node(objectName, object)
            self.nodes[objectName] = node
        else:
            node = self.nodes[objectName]
        return node

    def relationshipEdge(self, figure, relatedObjectName, label, fromNode):
        relatedObject = figure.objects[relatedObjectName]
        node = self.findOrCreateNode(relatedObjectName, relatedObject)
        edge = Edge(label, node)
        fromNode.addEdge(edge)

    def relationshipEdges(self, figure, objectName, label):
        object = figure.objects[objectName]
        node = self.findOrCreateNode(objectName, object)
        if label in object.attributes:
            relationNames = object.attributes[label]
            for relatedObjectName in relationNames.split(","):
                self.relationshipEdge(figure, relatedObjectName, label, node)

    def relationships(self, figure):
        for objectName in figure.objects:
            self.relationshipEdges(figure, objectName, "inside")
            self.relationshipEdges(figure, objectName, "above")

    def generateNodesAndRelationshipsFromFigure(self, figure):
        self.relationships(figure)

    def nodeNamed(self, name):
        return self.nodes[name]

    def compare(self, otherNodeSet):
        for nodeName in self.nodes:
            node = self.nodes[nodeName]
            otherNode = otherNodeSet.nodeNamed(nodeName)
            if node.sameEdges(otherNode) == False:
                return False



class Agent:
    # The default constructor for your Agent. Make sure to execute any
    # processing necessary before your Agent starts solving problems here.
    #
    # Do not add any variables to this signature; they will not be used by
    # main().
    def __init__(self):
        pass

    # The primary method for solving incoming Raven's Progressive Matrices.
    # For each problem, your Agent's Solve() method will be called. At the
    # conclusion of Solve(), your Agent should return an int representing its
    # answer to the question: 1, 2, 3, 4, 5, or 6. Strings of these ints 
    # are also the Names of the individual RavensFigures, obtained through
    # RavensFigure.getName(). Return a negative number to skip a problem.
    #
    # Make sure to return your answer *as an integer* at the end of Solve().
    # Returning your answer as a string may cause your program to crash.
    def Solve(self,problem):
        figures = problem.figures
        figureA = figures["A"]
        figureB = figures["B"]
        figureC = figures["C"]
        semnetAtoB = SemNet(figureA, figureB)
        semnetAtoC = SemNet(figureA, figureC)


        semnetCto1 = SemNet(figureC, figures["1"])
        semnetCto2 = SemNet(figureC, figures["2"])
        semnetCto3 = SemNet(figureC, figures["3"])
        semnetCto4 = SemNet(figureC, figures["4"])
        semnetCto5 = SemNet(figureC, figures["5"])
        semnetCto6 = SemNet(figureC, figures["6"])

        semnetBto1 = SemNet(figureB, figures["1"])
        semnetBto2 = SemNet(figureB, figures["2"])
        semnetBto3 = SemNet(figureB, figures["3"])
        semnetBto4 = SemNet(figureB, figures["4"])
        semnetBto5 = SemNet(figureB, figures["5"])
        semnetBto6 = SemNet(figureB, figures["6"])

        possibleAnswersC = {1:semnetCto1,
                            2:semnetCto2,
                            3:semnetCto3,
                            4:semnetCto4,
                            5:semnetCto5,
                            6:semnetCto6}

        possibleAnswersB = {1:semnetBto1,
                            2:semnetBto2,
                            3:semnetBto3,
                            4:semnetBto4,
                            5:semnetBto5,
                            6:semnetBto6}


        answer = possibleAnswersC #semnetAtoB.findAnswerFrom(possibleAnswersC)

        if len(answer) > 1 or len(answer) == 0:
            answer = possibleAnswersC
            expectNodeSetFromC = semnetAtoB.fromFigure(figureC)
            expectNodeSetFromB = semnetAtoC.fromFigure(figureB)
            for key in answer.copy():
                possibleAnswer = answer[key]
                if expectNodeSetFromC.compare(possibleAnswer.fromSet) == False:
                    if key in answer: del answer[key]

            if len(answer) > 1:
                for key in answer.copy():
                    if expectNodeSetFromB.compare(possibleAnswersB[key].fromSet) == False:
                        if key in answer: del answer[key]


        if len(answer) > 1 or len(answer) == 0:
            print "need to do something else"
            return -1
        else:
            return  answer.keys()[0]