from math import sqrt
import time

class Integration(object):
    
    def __init__(self, data):
        if data:
            self.data = data
            self.__len__ = len(data)

    def mean(self):
        """
        returns mean of a given list
        """

        return reduce(lambda x,y: x+y, self.data) / float(len(self.data))

    def rms(self):
        """
        returns root mean square of a given list
        """
        mean = self.mean()
        return sqrt(reduce(lambda x,y: x + (y - mean)**2, self.data) / float(self.__len__))

    def entries(self):
        """
        returns size of a given list
        """

        return self.__len__

    def result(self, definition=4):
        """
        returns Ys of a given list
        """

	start = time.time()

        self.data.sort()
        min = float(self.data[0])
        max = float(self.data[-1])
        step =  (max-min) / definition
        i = 0
        resultX = []
        resultY = []

        while (min < max):
            val = 0
            while (self.data[i] < min+step):
                val += 1
		"""
		if i == self.__len__-1:
		    break
		"""
		i += 1
                if i > self.__len__-1: 
                    break
            resultX.append(str(min))
            resultY.append(val)
            #result.append(((min,min+step),val))
            min += step

            if min == max:
                resultX.append(str(min))
                resultY.append(1)
                #result.append(((min,min+step),1))

	stop = time.time()

        return ([resultX, resultY], (stop-start))

if __name__=="__main__":
	testData = [1, 2, 2.5, 2.6, 3]
	test = Integration(testData)
	print "testData: " + str(testData)
	print "mean: " + str(test.mean())
	print "rms: " + str(test.rms())
	print "entries: " + str(test.entries())
	#print "result: \n" + reduce(lambda x, y: str(x) + "\n" + str(y), test.result(4))
	output	= test.result(124)
	print output

