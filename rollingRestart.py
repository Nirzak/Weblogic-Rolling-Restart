#############################################

# Author: Nirjas Jakilim

# Motive: Rolling restart the servers based on their machines.

# Usage: run "wlst.sh rollingRestart.py" to perform a full rolling restart.

# To restart particular servers run "wlst.sh rollingRestart.py <server names>"

# for example: wlst.sh rollingRestart.py wlms01 wlms02 and so on.

#############################################

shutMS=[] # Array to store the managed servers that have been shutdown

tasks=[] # Array to store server starting tasks.

connect('user','password','t3://<admin_server_url_here>:7001') # Connecting to our admin server domain

machines=cmo.getMachines() # Get and stores the MBean of the server machines.

machines.pop(0) # Will remove Admin Machine MBean from the list. This is done for safety purpose.

domainRuntime() # Navigating to domainRuntime directory. Must be done to capture the MBean of server runtimes.

n=len(sys.argv) # Storing number of server name arguments

# Condition to check if there are any arguments provided. If number of arguments is more than 1 then it will execute particular server restart otherwise it will execute full server Rolling Restart.
if n > 1:
	print ("Starting Specific Server Restart\n")

       	for server in range(1,n):
# Navigating to Server Life Cycle Runtimes directory of that particular server that is provided as our argument. for example: If we provide bdwlms01a it will execute cd ('/ServerLifeCycleRuntimes/bdwlms01a')
		cd ('/ServerLifeCycleRuntimes/'+sys.argv[server]);

# Condition to check if the server is running. If the server is running it will perform a full restart. Otherwise it will just attempt to start the server.
		if (cmo.getState()=='RUNNING'):
                	shutdown(sys.argv[server], 'Server', force='true')
                	start(sys.argv[server], 'Server')
		else:
			start(sys.argv[server], 'Server')

else:
	servers=cmo.getServerLifeCycleRuntimes() # Storing all the server runtimes MBean to array list
	servers.pop(0) # Removing the mbean of Admin Server

	serverConfig() # Navigating back to serverConfig directory from domainRuntime. This has to be done other wise we can't fetch server machines.

	print ("Starting Rolling Restart\n")

# Nested loop to check and shutdown the servers under a particular machine. Outer loop will go through all the machines and the inner loop will go through all the servers.
	for machine in machines:
		print ("Shutting down "+machine.getName()+" Servers\n")
		for server in servers: 
			ms = server.getName() # Storing the current managed server name to ms.

        		if ms != "AdminServer": # Admin Server checker is still here for the safety purpose

				cd('/Servers/'+ms) # Navigating to managed server's MBean directory

				current_machine=cmo.getMachine() # Storing the current managed server's assigned machine to current_machine variable.
				
# This condition will check if the current managed server's machine is the current machine that we are trying to restarting. If yes then the current managed server will shutdown for the restart. Otherwise it will ignore the other managed servers. 
				if (current_machine==machine):

                			shutdown(server.getName(), 'Server', force="true") # Shutting down managed server
					shutMS.append(server) # Storing the current shut down managed servers to start it later.
			else:
				print ("AdminServer - no action performed\n")

		print ("Starting "+machine.getName()+" Servers\n")

# This loop will basically go through all the shut down managed server inside shutMS list and append them to the task list so that they can concurrently start. 
		for MS in shutMS: 
			tasks.append(MS.start()) 
# If the number of tasks is not empty the following loop will execute to check whether they are completed or not.
		while len(tasks) > 0:
			for task in tasks:
        			if task.getStatus()  != "TASK IN PROGRESS" : # Checking the status of the task
            				tasks.remove(task) # Removing the task if completed

    			java.lang.Thread.sleep(5000) # Sleeping the concurrent thread.

# This loop will go through the shutMS list to check the status of the servers if they have started successfully or not. This is a final check. If any of the server has failed to start then the rolling process will be terminated.
		for MS in shutMS:
			if(MS.getState()!='RUNNING'):
				print ("One of the Server Failed to start. ABorting Rolling Restart.")
				disconnect()
				exit()
			else:
				shutMS.remove(MS) # Removing the managed server that have been started successfully from the shutMS list. 
		print (machine.getName()+" Servers started successfully\n")

# Disconnect and exit from the Admin Server domain
disconnect()
exit()

