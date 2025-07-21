from zeep import Client
from zeep.transports import Transport
from requests import Session

# WSDL URL provided by the service
wsdl_url = 'http://543.cgrate.co.zm:55555/Konik/KonikWs?WSDL'

session = Session()
session.verify = False 

transport = Transport(session=session)
# Load the SOAP client
client = Client(wsdl=wsdl_url, transport=transport)

# Get and print available services and operations
print("🧩 Available services and operations:\n")

# Loop through all services
for service in client.wsdl.services.values():
    print(f"📌 Service: {service.name}")
    
    # Loop through all ports in the service
    for port in service.ports.values():
        print(f"  ↳ Port: {port.name}")
        
        # Get operations for this port
        operations = port.binding._operations
        
        print("    📄 Operations (methods):")
        for operation_name, operation in operations.items():
            # Print method name and parameters
            print(f"     🔹 {operation_name}({operation.input.signature()})")

# You can also list all bindings
print("\n🔧 Raw method names:")
print(client.wsdl.bindings)
