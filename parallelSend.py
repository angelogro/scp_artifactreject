import sys
from threading import Event, Timer

class ParallelSender():
    def __init__(self):
        if sys.platform == 'win32':
            try:
                from ctypes import windll
                self.pport = windll.LoadLibrary('inpoutx64.dll')
            except:
                print("Could not load inpout32.dll. Please make sure it is located in the system32 directory")
        else:
            try:
                import parallel
                self.pport = parallel.Parallel()
            except:
                print("Unable to open parallel port! Please install pyparallel to use it.")
        size_argv = len(sys.argv);
        
        self.triggerResetTime = 0.01
        if(size_argv>1):
            self.port_num=int(sys.argv[1],16);
        else:
            self.port_num=0x3010;


    def send_parallel(self,data, reset=True):
    
        """Sends the data to the parallel port."""
        
        ### HAS TO BE ERASED WHEN PARALLEL PORT WORKS FINE
        print(data)
        #return
        
        
        
        if reset == True:
            # A new trigger arrived before we could reset the old one
            if hasattr(self,'triggerResetTimer'):
                self.triggerResetTimer.cancel()
        if self.pport:
            if sys.platform == 'win32':
                self.pport.Out32(self.port_num, data)
            else:
                self.pport.setData(data)
            if reset:
                self.triggerResetTimer = Timer(self.triggerResetTime, self.send_parallel, (0, False))
                self.triggerResetTimer.start()


