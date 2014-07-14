# Configuration settings
rhizomatica_dir = '/var/rhizomatica'
sq_hlr_path = '/var/lib/osmocom/hlr.sqlite3'

# database
pgsql_db = 'rhizomatica'
pgsql_user = 'rhizomatica'
pgsql_pwd = 'xEP3Y4W8gG*4*zu'
pgsql_host = 'localhost'

# SITE
site_name = "Test"
postcode = "12345"
pbxcode = "1"
# network name
network_name = "TestNetwork"
# VPN ip address
ip_address = "10.66.0.14"
wan_ip_address = "192.168.1.99"

# SITE settings
# rate type can be "call" or "min"
limit_local_calls = 1    
limit_local_minutes = 5  
charge_local_calls = 0   
charge_local_rate = ""   
charge_local_rate_type = ""
charge_internal_calls = 0  
charge_internal_rate = ""  
charge_internal_rate_type = ""
charge_inbound_calls = 0
charge_inbound_rate = ""          
charge_inbound_rate_type = ""      
smsc_shortcode = "10000"
sms_sender_unauthorized = 'Tu usuario no está autorizado en esta red. Por favor registre su teléfono.'
sms_destination_unauthorized = 'Este usuario no se ha registrado. Él no va a recibir su mensaje.'

rmai_admin_user = "admin"
rmai_admin_pwd = ',.admin1'

kannel_server = '127.0.0.1'
kannel_port = 14002
kannel_username = 'rhizomatica'
kannel_password = 'Nan3RZhekZy0'

# VOIP provider
provider_name = "provider"
username = "6142088545"
from-user = "6142088545"
password = "1469"
proxy = "169.132.196.11"
did = "6142088545"
cli = "525541703851"

# Subscription SMS notification
notice_msg = 'Favor de pagar su cooperacion mensual de 30 pesos. Gracias.' 
reminder_msg = 'Recuerda: su servicio sera desactivado si no paga su cuota antes del 7 de cada mes. Gracias.' 
deactivate_msg = 'Su servicio ha sido desactivado hasta que haga su cooperacion mensual.'
