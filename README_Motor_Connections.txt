Setting up the Areotech motor communications:

To setup the motor connections in Ensemble:
    - The LAN should have the following:
        IP Address: 192.168.1.4
        Subnet mask: 255.255.255.0
        Default gateway: 192.168.1.1
        Preferred DNS: Empty
        Alternate DNS: Empty
    - In the Configuration Manager provide the motor with:
        IP Addres: 192.168.1.2
        Subnet mask: 255.255.255.0
        Default gateway: 192.168.1.1

After this setup, you should be able to connect to the motor over the ethernet cable
by simply selecting the Connect button.

To setup the motor to communicate over ethernet:

    -Perform the same setup as above - this ensures the correct IP addresses
    -Connect to the controller
    -Right click the controller and select Retrieve Parameters
    -Under the controller name expand the Parameters folder
    -Go to System>Communications>Ethernet Sockets
    -Update the parameters with the following information:
        - Socket2Port: 8000
        - Socket2RemoteIPAddress: 0.0.0.0
        - Socket2Setup: TCP Server (the motor will listen for commands)
        - Socket2Timeout: 1000 (in seconds)
        - Socket3Port: 8001
        - Socket3RemoteIPAddress: 0.0.0.0
        - Socket3Setup: TCP Server
        - Socket3Timeout: 1000 (in seconds)        
    -Go to System>Communication>ASCII
    -Update the parameters with the following information:
        - CommandSetup: Ethernet Socket2 & Ethernet Socket3
            - Enable Multi-Command
            - 0x0003000C is the final parameter value
        - CommandTimeout: 1000000 (in milliseconds)
    -Keep the command characters as defaults results in:
        - Fault Character: #
        - Invalid Character: !
        - Success Character: %
        - Terminating Character: \n (character at end of each string)
        - Timeout Character: $
    -Right click and select Commit Parameters
    -These were also updated in the 181711-A-1-1.prme parameter file

    
This will allow the motor to communicate through Python using the socket module
and should improve the speed with the motor communication since we tell it to 
listen only on the Ethernet2 line.

More details and examples of the available functions can be found at:
    Programming>AeroBasic>Communication>ASCII Command Interface>ASCII Command Interface



