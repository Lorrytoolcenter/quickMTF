Copyright (c) 2021 lorry_rui , Newark ,USA  

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute,  and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
 The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

 
*for image quaility test purpose like lens focus test   @  Lorry RUi  

Main feature for this package	
============================  

	1) can quick get  MTF value bother for linepair or slant edge MTF
	2)  
	3)  
	4)  
	5)  
	6)  
		
____________________________________	


Mail to: :lorryruizhihua@gmail.com  



sample code for using lib quickMTF


.. code-block:: python

   from quickMTF.quickMTF import quickMTF
   import cv2

   if __name__ == '__main__':
       test = quickMTF()
       ROI_width = 600
       ROIX = 1593
       ROIY = 1500
       image = cv2.imread("image.jpg")
       image = image[ROIY:ROIY+10, ROIX:ROIX+ROI_width]

       print(test.quicklinepairMTF(image, library='cv2'))  # linepair chart MTF value and pixels/line pair
       print(test.quicksfrMTF(image, cp=0.5))  # CP means cycles/pixel and out MTF value per c/p and slant angle
       print(test.quicksfrCP(image, mtf_indx=30))  # MTFindex means MTF and out Cycles/pixel per MTF value and slant angle

	
	
	
	
	
