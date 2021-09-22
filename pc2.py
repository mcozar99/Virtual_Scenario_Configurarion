from subprocess import call
from lxml import etree
import sys

nas = ['nas1', 'nas2', 'nas3'] #variable global que contiene el nombre de los almacenes nas


def numServidores():
    # Devuelve el array de servidores creados
    f=open('nserv.cfg','r')
    num_serv = ''
    for line in f:                  # Leemos el numero de servidores que tenemos en el fichero cfg
        if 'num_serv' in line:
            num_serv = line.split('=')[1]
    f.close()
    i = 1
    srv= []

    while i <= int(num_serv):   # Los metemos a la lista con su nombre correspondiente
        a = 's' + str(i)
        srv.append(a)
        i += 1    
    return srv


def serverConfigurados():
    # Devuelve el array de servidores configurados con quiz
    f=open('nserv.cfg','r')
    num_serv = ''
    for line in f:                  # Leemos el numero de servidores configurados que tenemos en el fichero cfg
        if 'quiz_instalado' in line:
            num_serv = line.split('=')[1]
        
    f.close()
    i = 1
    srv= []
    while i <= int(num_serv):   # Los metemos a la lista con su nombre correspondiente
        a = 's' + str(i)
        srv.append(a)
        i += 1    
    return srv


def algoritmos():
    # Devuelve el array con los posibles algoritmos de balanceo alojados en el fichero de configuracion
    f = open('nserv.cfg', 'r')
    algoritmos = []
    for line in f:
        if 'algoritmos' in line:
            algoritmos = line.replace(' ', '').replace('\n', '').split('=')[1].split(',')
    f.close()
    return algoritmos

def configura(total, instalados):
    # Edita el numero de servidores creados e instalados con quiz rapidamente
    f = open('nserv.cfg', 'w')
    f.write('num_serv=%s\n'%total)
    f.write('quiz_instalado=%s\n'%instalados)
    f.write('algoritmos=roundrobin, leastconn, source, static-rr')
    f.close()

def creaServidores(num_serv):
    # Crea tantos servidores como se le indique en base a modificar el fichero s4.xml
    srv= numServidores()
    instalados = serverConfigurados()
    for i in range(srv.__len__()+1, srv.__len__() + int(num_serv) + 1):
        # Para cada server nuevo creamos un nuevo fichero xml con el nombre del nuevo server y modificamos sus direcciones y nombres
        call('cp s4.xml s%s.xml'%i, shell=True)
        tree = etree.parse('s%s.xml'%i)
        root = tree.getroot()
        root.find("global/scenario_name").text = "cdps_pc2_s%s"%i
        vm = root.find("vm")
        vm.set('name', 's%s'%i)
        vm.find("if[@id='1']/ipv4").text='20.20.3.1%s/24'%i
        vm.find("if[@id='2']/ipv4").text='20.20.4.1%s/24'%i
        f = open('s%s.xml'%i, "w")
        f.write(etree.tounicode(tree, pretty_print=True))
        f.close()
        call('sudo vnx -f s%s.xml --create'%i, shell=True)
    # Modificamos el fichero de configuracion para anadir los nuevos servidores
    configura(srv.__len__() + int(num_serv), instalados.__len__())
    
                
def descarga():
    # Obtiene el escenario y lo prepara para su ejecucion
    call('wget http://idefix.dit.upm.es/cdps/pc2/pc2.tgz', shell=True)
    call('sudo vnx --unpack pc2.tgz', shell=True)
    call('cd pc2; bin/prepare-pc2-vm', shell = True)
    call('mv pc2.py pc2', shell=True)
    call('mv fw.fw pc2', shell=True)
    call('mv haproxy.cfg pc2', shell=True)
    call('mv nserv.cfg pc2', shell=True)
    call('mv reset.fw pc2', shell=True)
    print('\n\nEjecute \'$ cd pc2\' para seguir ejecutando acciones correctamente\n\n')


def arrancaEscenario():
    # Arranca una o todas las maquinas virtuales
    if sys.argv.__len__() == 2:
        call('sudo vnx -f pc2.xml --create', shell=True)
        call('sudo vnx -f s4.xml --create', shell=True)
    elif sys.argv[2] != None:
        call('sudo vnx -f %s.xml --create' %sys.argv[2], shell=True)
    else:
        call('sudo vnx -f pc2.xml --create -M %s' %sys.argv[2], shell=True)


def paraMaquina():
    # Para una o todas las maquinas virtuales
    if sys.argv.__len__() == 2:
        call('sudo vnx -f pc2.xml --shutdown', shell=True)
        call('sudo vnx -f s4.xml --shutdown', shell=True)
    elif sys.argv[2] == 's4':
        call('sudo vnx -f s4.xml --shutdown -M %s' %sys.argv[2], shell=True)
    else:
        call('sudo vnx -f pc2.xml --shutdown -M %s' %sys.argv[2], shell=True)


def destruyeMaquina():
    num_serv = numServidores().__len__()
    # Destruye una o todas las maquinas virtuales
    if sys.argv.__len__() == 2:
        call('sudo vnx -f pc2.xml --destroy', shell=True)
        for i in range(4, num_serv+1):
            call('sudo vnx -f s%s.xml --destroy'%i, shell=True)
        for i in range(5, num_serv+1):
            call('rm s%s.xml'%i, shell=True) #Borramos los xml de los servidores que no son originales
        configura(4, 0)
    elif sys.argv[2] == 's4':
        call('sudo vnx -f s4.xml --destroy', shell=True)
    elif sys.argv[2] != 's4' and sys.argv.__len__() == 3:
        call('sudo vnx -f %s.xml --destroy %s' %(sys.argv[2], sys.argv[2]), shell=True)
        print(sys.argv[2])
        call('rm %s.xml'%sys.argv[2], shell=True)
        

def configuraFW():
    #Copia y ejecuta el fichero fw.fw creado previamente con fwbuilder para permitir solo trafico tcpy ping al lb
    #Previamente a la ejecucion se otorgan permisos de ejecucion para el fichero
    call("(sudo /lab/cdps/bin/cp2lxc fw.fw /var/lib/lxc/fw/rootfs/etc)", shell=True)
    call("(sudo lxc-attach --clear-env -n fw -- bash -c \"mkdir fw1; cp /etc/fw.fw /fw1\")", shell=True)
    call("(sudo lxc-attach --clear-env -n fw -- bash -c \"cd /fw1; chmod 777 fw.fw; ./fw.fw\")", shell=True)


def resetFW():
   #Hace que el fw permita cualquier tipo de trafico, usado para tareas de control
   #Mismo funcionamiento que el configura fw
   call("(sudo /lab/cdps/bin/cp2lxc reset.fw /var/lib/lxc/fw/rootfs/etc)", shell=True)
   call("(sudo lxc-attach --clear-env -n fw -- bash -c \"mkdir fw1; cp /etc/reset.fw /fw1\")", shell=True)
   call("(sudo lxc-attach --clear-env -n fw -- bash -c \"cd /fw1; chmod 777 reset.fw; ./reset.fw\")", shell=True)


def configuraBBDD():
    srv = numServidores()
    #Comandos de configuracion en la maquina vitual BBDD para configurar la base de datos
    call("(apt update)", shell=True)
    call("(sudo lxc-attach --clear-env -n bbdd -- apt -y install mariadb-server)", shell=True)
    call("(sudo lxc-attach --clear-env -n bbdd -- sed -i -e 's/bind-address.*/bind-address=0.0.0.0/' -e 's/utf8mb4/utf8/' /etc/mysql/mariadb.conf.d/50-server.cnf)", shell=True)
    call("(sudo lxc-attach --clear-env -n bbdd -- systemctl restart mysql)", shell=True)
    call("(sudo lxc-attach --clear-env -n bbdd -- mysqladmin -u root password xxxx)", shell=True)
    call("(sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"CREATE USER 'quiz' IDENTIFIED BY 'xxxx';\")", shell=True)
    call("(sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"CREATE DATABASE quiz;\")", shell=True)
    call("(sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"GRANT ALL PRIVILEGES ON quiz.* to 'quiz'@'localhost'IDENTIFIED by'xxxx';\")", shell=True)
    call("(sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"GRANT ALL PRIVILEGES ON quiz.* to 'quiz'@'%' IDENTIFIED by 'xxxx';\")", shell=True)
    call("(sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"FLUSH PRIVILEGES;\")", shell=True)
    #Instalamos mariadb-client en los servidores
    for server in srv:
        call("(sudo lxc-attach --clear-env -n %s -- apt -y install mariadb-client)"%server, shell=True) 


def configuraGluster():
    # Configuracion de los servidores de disco (nas)
    call("(sudo lxc-attach --clear-env -n nas1 -- gluster peer probe 20.20.4.22)", shell=True)
    call("(sudo lxc-attach --clear-env -n nas1 -- gluster peer probe 20.20.4.23)", shell=True)
    for nases in nas:
        call("(sudo lxc-attach --clear-env -n %s -- mkdir nas)" %nases, shell=True)
    # Mejora de la replica, metemos replica 3 para proteccion ante fallos
    call("(sudo lxc-attach --clear-env -n nas1 -- gluster volume create nas replica 3 transport tcp nas1:/nas nas2:/nas nas3:/nas force)", shell=True)
    call("(sudo lxc-attach --clear-env -n nas1 -- gluster volume start nas)",shell=True)
    call("(sudo lxc-attach --clear-env -n nas1 -- gluster volume set nas network.ping-timeout 5)", shell=True)


def destruyeGluster():
    # Solucion de un fallo del escenario que no borra los directorios creados en los nas y dificulta el rearranque
    call("(sudo lxc-attach --clear-env -n nas1 -- gluster volume stop nas)",shell=True)
    call("(sudo lxc-attach --clear-env -n nas1 -- gluster volume delete nas force)", shell=True)
    for nases in nas:
        call("(sudo lxc-attach --clear-env -n %s -- rm -rfv nas)" %nases, shell=True)


def instalaQuiz():
    # Instala y configura la aplicacion QUIZ en los servidores
    # Para optimizar el funcionamiento del script solo instalamos quiz en los servidores que no lo tengan instalado
    totales = numServidores()
    instalados = serverConfigurados()
    srv = list(set(instalados) ^ set(totales))

    # 1- Clonamos el repositorio en los servidores
    for server in srv:
        call("(sudo lxc-attach --clear-env -n %s -- bash -c \"mkdir quiz; cd quiz; git clone https://github.com/CORE-UPM/quiz_2021.git\")"%server, shell=True)

    # 2- Borramos la linea de redirect en app.js de cada server y anadimos a cada servidor en index.ejs su nombre para comprobar el balanceo
    for server in srv:
        call("(sudo lxc-attach --clear-env -n %s -- bash -c \"cd /quiz/quiz_2021; sed -i \"29d\" app.js\")"%server, shell=True)
        call("(sudo lxc-attach --clear-env -n %s -- bash -c \"cd /quiz/quiz_2021/views; echo \"%s\" >> index.ejs\")"%(server,server), shell=True)

    # 3- Instalamos las dependencias necesarias
    for server in srv:
        call("(sudo lxc-attach --clear-env -n %s -- bash -c \"cd /quiz/quiz_2021; npm install; npm install forever; npm install mysql2; export QUIZ_OPEN_REGISTER=yes\")"%server, shell=True)

    # 4- Exportamos la DATABASE_URL en los servidores y aplicamos la migracion y los seeders en s1
    for server in srv:
        if server == 's1':
            call("(sudo lxc-attach --clear-env -n s1 -- bash -c \"cd /quiz/quiz_2021; export DATABASE_URL=mysql://quiz:xxxx@20.20.4.31:3306/quiz; npm run-script migrate_env; npm run-script seed_env\")",shell=True)
        else:
            call("(sudo lxc-attach --clear-env -n %s -- bash -c \"cd /quiz/quiz_2021; export DATABASE_URL=\"mysql://quiz:xxxx@20.20.4.31:3306/quiz\" \")"%server, shell= True)

    # 5- Hacemos el mount del public/uploads en el gluster, lo creamos e instalamos tambien las dependencias
    for server in srv:
        call("(sudo lxc-attach --clear-env -n %s -- bash -c \"cd /quiz/quiz_2021; mkdir -p public/uploads; npm install; npm install forever; npm install mysql2\")"%server, shell=True)
        call("(sudo lxc-attach --clear-env -n %s -- bash -c \"cd /quiz/quiz_2021; mount -t glusterfs 20.20.4.21:/nas public/uploads\")"%server, shell=True)

    # 6- Arrancamos la aplicacion quiz en cada server
    for server in srv:
        call("(sudo lxc-attach --clear-env -n %s -- bash -c \"cd /quiz/quiz_2021; export DATABASE_URL=mysql://quiz:xxxx@20.20.4.31:3306/quiz; ./node_modules/forever/bin/forever start ./bin/www\")"%server, shell=True)

    # Actualizamos el fichero de configuracion para anadir los nuevos servidores creados
    configura(totales.__len__(), totales.__len__())


def configuraHAProxy(balanceo):
    # Pone en marcha el balanceo en el lb, con el algoritmo de balanceo que le indiquemos
    srv = serverConfigurados()
    call("(cp haproxy.cfg haproxyaux.cfg)", shell=True)
    f = open('haproxyaux.cfg', 'a')     #fichero plantilla de conf del haproxy
    f.write('\tbalance %s \n'%balanceo)      #seleccionamos el tipo de balanceo que queremos
    # Metemos en el fichero haproxy los servidores que tengan quiz instalado
    for server in srv:
        f.write('\tserver %s 20.20.3.1%s:3000 check\n'%(server, server[1]))
    f.close()
    # Movemos nuestro fichero haproxy.cfg al directorio /etc/haproxy de lb, instalamos dependencias y arrancamos el servicio
    call("(sudo lxc-attach --clear-env -n lb -- service apache2 stop)", shell=True)
    call("(sudo lxc-attach --clear-env -n lb -- mkdir /etc/haproxy)", shell=True)
    call("(sudo lxc-attach --clear-env -n lb -- sudo apt-get install haproxy)", shell=True)
    call("(sudo /lab/cdps/bin/cp2lxc haproxyaux.cfg /var/lib/lxc/lb/rootfs/etc/haproxy/haproxy.cfg)", shell=True)
    call("(sudo lxc-attach --clear-env -n lb -- sudo service haproxy restart)", shell=True)
    call("(rm haproxyaux.cfg)", shell=True)


def ping():
    # Comprueba la conectividad desde el host a cada LAN para ver si nuestro firewall funciona correctamente
    ips = ['20.20.1.11', '20.20.2.2', '20.20.3.11', '20.20.4.21']
    for ip in ips:
        indice = str(ips.index(ip) + 1)
        print("PING A LAN%s"%indice)
        call("(ping -c 3 -W 2 %s)"%ip, shell = True)
        print('\n\n')

#Lista de posibles acciones a realizar

if sys.argv[1] == 'descarga':
    descarga()

elif sys.argv[1] == 'create':
    numServidores()
    arrancaEscenario()

elif sys.argv[1] == 'stop':
    paraMaquina()

elif sys.argv[1] == 'destroy':
    if sys.argv.__len__() == 2:
        destruyeGluster()    
    destruyeMaquina()

elif sys.argv[1] == 'gluster':
    configuraGluster()

elif sys.argv[1] == 'bbdd':
    configuraBBDD()

elif sys.argv[1] == 'quiz':
    instalaQuiz()

elif sys.argv[1] == 'lb':
    configuraHAProxy()

elif sys.argv[1] == 'haproxy':
    # Seleccionamos el tipo de balanceo a elegir, por defecto se implanta roundrobin
    if sys.argv.__len__() == 2:
        configuraHAProxy('roundrobin')
    elif sys.argv.__len__() == 3 and sys.argv[2] in algoritmos():
        configuraHAProxy(sys.argv[2])
    else:
        print('Introduzca un balanceo valido entre los siguientes %s'%algoritmos())

elif sys.argv[1] == 'fw':
    #Aqui podemos decidir si configuramos el firewall como nos indica la mejora de la pc2 o lo reseteamos y permitimos todos
    #los traficos posibles (con la opcion reset)
    if sys.argv.__len__() == 2:
        configuraFW()
    elif sys.argv.__len__() == 3 and sys.argv[2] == 'reset':
        resetFW()

elif sys.argv[1] == 'server':
    creaServidores(sys.argv[2])

elif sys.argv[1] == 'escenario':
    arrancaEscenario()
    configuraFW()
    configuraBBDD()
    configuraGluster()
    instalaQuiz()
    configuraHAProxy('roundrobin')

elif sys.argv[1] == 'ping':
    ping()


elif sys.argv[1] == 'help':
    print('\n\nMANUAL DE INSTRUCCIONES')
    print('\n\tdescarga - Descarga el archivo comprimido que contiene el escenario de la practica')
    print('\n\tcreate (X)- Crea y arranca las maquinas virtuales del escenario con 4 servidores o una maquina concreta')
    print('\n\tstop (X)- Para las maquinas virtuales del escenario o una maquina concreta')
    print('\n\tdestroy (X)- Destruye el escenario o una maquina concreta')
    print('\n\tescenario - Realiza todas las instalaciones y configuraciones de forma que el escenario sea totalmente operativo con balanceo Round-Robin y 4 servers')
    print('\n\tbbdd - Crea y configura la base de datos, con las instalaciones de dependencias necesarias.')
    print('\n\tgluster - Crea y arranca el almacenamiento con gluster')
    print('\n\thaproxy (X) - Configura el balanceador de trafico con el algoritmo X de entre los posibles (oundrobin, leastconn, source, static-rr). Por defecto Round-Robin. ')
    print('\n\tfw (reset)- Configura el firewall a partir del fw.fw de forma que solo se permita acceder al balanceador por TCP puerto 80 y por ping. Opcion reset para permitir cualquier trafico')
    print('\n\tquiz - Instala el servicio Quiz en todos los servidores en los que no haya sido instalado previamente')
    print('\n\tserver X - Crea y arranca X servidores adicionales')
    print('\n\tping - Realiza una prueba de conectividad a cada red del escenario\n')







    
