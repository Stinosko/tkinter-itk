import threading

class TkRepeatingTask():

    def __init__( self, tkRoot, taskFuncPointer, freqencyMillis ):
        self.__tk_   = tkRoot
        self.__func_ = taskFuncPointer        
        self.__freq_ = freqencyMillis
        self.__isRunning_ = False

    def isRunning( self ) : return self.__isRunning_ 

    def start( self ) : 
        self.__isRunning_ = True
        self.__onTimer()

    def stop( self ) : self.__isRunning_ = False

    def __onTimer( self ): 
        if self.__isRunning_ :
            self.__func_() 
            self.__tk_.after( self.__freq_, self.__onTimer )

class BackgroundTask():

    def __init__( self, taskFuncPointer ):
        self.__taskFuncPointer_ = taskFuncPointer
        self.__workerThread_ = None
        self.__isRunning_ = False

    def taskFuncPointer( self ) : return self.__taskFuncPointer_

    def isRunning( self ) : 
        return self.__isRunning_ and self.__workerThread_.is_alive()

        """Exception has occurred: AttributeError
'WorkerThread' object has no attribute 'isAlive'
  File "C:\SSD\projects\TK-MedSAM\threading_tk.py", line 34, in isRunning
    return self.__isRunning_ and self.__workerThread_.isAlive()
  File "C:\SSD\projects\TK-MedSAM\ITKviewerframe.py", line 520, in update_image_if_needed
    if self.bgTask.isRunning():
  File "C:\SSD\projects\TK-MedSAM\ImagesFrameManager.py", line 147, in update_images_if_needed_from_nested_list
    sub_item.update_image_if_needed()
  File "C:\SSD\projects\TK-MedSAM\ImagesFrameManager.py", line 198, in update_image_if_needed
    update_images_if_needed_from_nested_list(self.images_labels)
  File "C:\SSD\projects\TK-MedSAM\ITK_viewer.py", line 159, in update
    self.ITKviewer.update_image_if_needed()
  File "C:\SSD\projects\TK-MedSAM\ITK_viewer.py", line 172, in <module>
    app.update()
AttributeError: 'WorkerThread' object has no attribute 'isAlive'"""
    def start( self ): 
        if not self.__isRunning_ :
            self.__isRunning_ = True
            self.__workerThread_ = self.WorkerThread( self )
            self.__workerThread_.start()

    def stop( self ) : self.__isRunning_ = False

    class WorkerThread( threading.Thread ):
        def __init__( self, bgTask ):      
            threading.Thread.__init__( self, daemon=True )
            self.__bgTask_ = bgTask

        def run( self ):
            try :
                self.__bgTask_.taskFuncPointer()( self.__bgTask_.isRunning )
            except Exception as e: print( repr(e), "in threading_tk.py")
            self.__bgTask_.stop()