Usage
=====

Installation
~~~~~~~~~~~~

To run the current version you should pull the default branch. The `github page is here 
<https://github.com/Einstein42/lifx-nodeserver>`_.

.. code-block:: bash

    # Install the bitstring required package this is needed for talking to the LIFXLan protocols
	sudo pip install bitstring
	
    # Go to your Polyglot/config/node_servers/ folder
	git clone https://github.com/Einstein42/lifx-nodeserver.git
	
    # Restart Polyglot to recognize the new Node Server type.
	sudo systemctl restart polyglot

Now that Polyglot is restarted. Login to your Polyglot admin page::

    http://<ip address>:8080

Add Node Server
~~~~~~~~~~~~~~~
.. image:: _static/add_nodeserver.png
   :scale: 50 %
   :align: center

Click on Add Node Server once you login to your Polyglot admin interface. Select the
LIFX node server type. Name it something logical... like LIFX, and select
a node server id between 1-10 that is currently unused in both Polyglot and the ISY.

.. image:: _static/add_nodeserver_2.png
   :scale: 50 %
   :align: center

Once the nodeserver is active you will see its status as 'running' in the top left corner. Under 
the name in bold, you will notice the node server number, in this case 1 and the Base URL.
Click the down arrow icon to download the profile.zip to your desktop, which we will import
into the ISY shortly. Copy the Base URL to your clipboard and remember the ID number then 
login to the ISY.

.. image:: _static/nodeserver.png
   :scale: 50 %
   :align: center

In the ISY click on the **Node Servers** menu option, then configure and finally the ID
number you remembered from the previous step and Network Connection.

Profile name does not have to be the same as the node server name in Polyglot, but it makes
sense to make them match. UserID and Password are the login credentials of the Polyglot 
admin. Base URL we copied from Polyglot in the step above. Host name and port are the
IP and port you used to connect to the Polyglot admin page. Leave SSL unchecked, Timeout 
and Isy User leave at 0.

Click the **Upload Profile** button at the bottom and select the profile.zip that we downloaded
from Polyglot.

.. image:: _static/isy_node.png
   :scale: 75 %
   :align: center

Now reboot the ISY by going to *Configuration* > *System* > *Reboot*.

Once the ISY is back up, restart Polyglot.

.. code-block:: bash

    sudo systemctl restart polyglot

You should now see the LIFX devices start populating is the ISY for consumption in programs. Enjoy!