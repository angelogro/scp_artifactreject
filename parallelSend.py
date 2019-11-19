import sys
from threading import Event, Timer

class ParallelSender():
    def __init__(self):
        if sys.platform == 'win32':
            try:
                from ctypes import windll
                self.pport = windll.inpout32
            except:
                print("Could not load inpout32.dll. Please make sure it is located in the system32 directory")
        else:
            try:
                import parallel
                self.pport = parallel.Parallel()
            except:
                print("Unable to open parallel port! Please install pyparallel to use it.")
        size_argv = len(sys.argv);
        
        self.triggerResetTime = 0.1
        if(size_argv>1):
            self.port_num=int(sys.argv[1],16);
        else:
            self.port_num=0x378;


    def send_parallel(self,pport, port_num, data, reset=True):
    
        """Sends the data to the parallel port."""
        
        ### HAS TO BE ERASED WHEN PARALLEL PORT WORKS FINE
        print(data)
        return
        
        
        
        if reset == True:
            # A new trigger arrived before we could reset the old one
            if hasattr(self,'triggerResetTimer'):
                self.triggerResetTimer.cancel()
        if pport:
            if sys.platform == 'win32':
                pport.Out32(port_num, data)
            else:
                pport.setData(data)
            if reset:
                self.triggerResetTimer = Timer(self.triggerResetTime, self.send_parallel, (pport,port_num,0x0, False))
                self.triggerResetTimer.start()

