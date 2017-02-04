import hashlib
import mimetypes,os
import keystoneclient.v3 as keystoneclient
import swiftclient.client as swiftclient
import MySQLdb
from flask import Flask, request, make_response,url_for,redirect
#from subprocess import call
from datetime import datetime
from dateutil import tz

from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher_suite = Fernet(key)



# auth_url = "https://identity.open.softlayer.com/v3"
# password = "O6YQL#0RxHq0Y9.6"
# project_id = "21b7016b23514c6899f353cb49136d10"
# region_name = "dallas"
# user_id = "7b129f43d4d14581b71b625e3a024aab"




#conn = swiftclient.Connection(key=password, authurl=auth_url, auth_version='3', os_options={"project_id":project_id, "user_id":user_id, "region_name":region_name})
#print('Connection successful.')

app = Flask(__name__)
#gpg = gnupg.GPG(gnupghome="C:\Program Files (x86)\GNU\GnuPG")
#gpg = gnupg.GPG(gnupghome="C:\Python27\Lib\site-packages")
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
ukey = ''


@app.route('/')
def Welcome():
    return app.send_static_file('index_login.html')


@app.route('/upload', methods=['POST', 'GET'])
def upload():
	if request.method == 'POST':
		
		db = MySQLdb.connect("us-cdbr-iron-east-04.cleardb.net","bb502b604c0f43","d302d795","ad_a09e2e841ca1aaf")
		cursor = db.cursor()
		
		file = request.files['file']
		desc = request.form['desc']
		file_contents = file.read()
		hash = hashlib.md5(file_contents).hexdigest()
		version = 1
		filename, file_extension = os.path.splitext(file.filename)
		size=len(file_contents);

		if(size > (1024*1024)):
			print 'File ', file.name, 'exceed 1MB redirecting!!'
			return redirect(url_for('list'))
		
		sql = "select id, hash from files where id = '"+filename+"_v"+str(version)+file_extension+"'"
		print sql
		cursor.execute(sql)
		results = cursor.fetchall()
		if cursor.rowcount==1:
			for row in results:
				if row[1]==hash:
					return 'The file already exists in the database.'
				else:
					version = version + 1
		
		sql = "insert into files values ('"+filename+"_v"+str(version)+file_extension+"','"+hash+"',"+str(version)+",'"+desc+"','hani',%s,"+str(size)+")"
		cursor.execute(sql, (file,))			
		db.commit()
		cursor.close()
		
		return redirect(url_for('list'))

@app.route('/eupload', methods=['POST', 'GET'])
def eupload():
	if request.method == 'POST':
		container_name = 'Encrypted'
		
		conn.put_container(container_name)
		print'A new container ',container_name,' was created successfully.'
		
		file = request.files['efile']
		#ukey = request.form['key']
		file_contents = file.read()
		mime_type = mimetypes.guess_type(file.filename)
		encrypted_file_name = 'e_'+file.filename
		size=len(file_contents);

		if(size > (1024*1024)):
			print 'File ', file.name, 'exceed 1MB redirecting!!'
			return redirect(url_for('list'))
		# print size
		
		print('Encrypting file...')
		#input_data = gpg.gen_key_input(key_type="RSA", key_length=1024, passphrase=ukey)
		#key = gpg.gen_key(input_data)
			
		#status = gpg.encrypt(file_contents,recipients=['aishwarya.vaidyanathan@mavs.uta.edu'])
		cipher_text = cipher_suite.encrypt(file_contents)
		print('File encrypted successfully.')
			
		# conn.put_object(container_name, 'encrypted'+file.filename, contents=str(status), content_type='text/plain')
		# print'File ',file.filename,' uploaded successfully.'
		conn.put_object(container_name, encrypted_file_name,cipher_text, content_type='text/plain')
		print'File ',encrypted_file_name,' uploaded successfully.', 'size of file', size

		
		for container in conn.get_account()[1]:
			for data in conn.get_container(container['name'])[1]:
				from_zone = tz.tzutc()		#tz.gettz('UTC')
				to_zone = tz.tzlocal()		#tz.gettz('US/Central')
				new_date = datetime.strptime(data['last_modified'], '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=from_zone).astimezone(to_zone)
				print'File Name: {0}\nFile Size: {1}\nLast Modified Date (GMT): {2}\nLast Modified Date (CST): {3}'.format(data['name'],data['bytes'],data['last_modified'], new_date)
		
#		return 'Encrypted file was uploaded successfully.'
		return redirect(url_for('list'))
		
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# hostname,username,password,dbname
		db = MySQLdb.connect("us-cdbr-iron-east-04.cleardb.net","bb502b604c0f43","d302d795","ad_a09e2e841ca1aaf")
		cursor = db.cursor()
		username = request.form['username']
		password = request.form['password']
	  
		sql = "select username, password from users where username = '"+username+"' and password = '"+password+"'"
		cursor.execute(sql)
		if cursor.rowcount == 1:
			results = cursor.fetchall()
			for row in results:
				if password == row[1]:
					return app.send_static_file('index_8.html')
		else:
			return app.send_static_file('index_login.html')
	else:
		return app.send_static_file('index_login.html')

			
# @app.route('/list', methods=['POST', 'GET'])
# def list():
	# list = ''
	# for container in conn.get_account()[1]:
		# list = list + '<br><br>Container : ' + container['name'] +'<br><br>'
		# for data in conn.get_container(container['name'])[1]:
			# from_zone = tz.tzutc()		#tz.gettz('UTC')
			# to_zone = tz.tzlocal()		#tz.gettz('US/Central')
			# new_date = datetime.strptime(data['last_modified'], '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=from_zone).astimezone(to_zone)
			# list = list + "<a href='download?id="+data['name']+"&cn="+container['name']+"'>"+data['name']+"</a>&nbsp;&nbsp;&nbsp;Size = "+str(data['bytes'])+" Last Modified Date "+ str(data['last_modified']) +" Last Modified Date (CST) "+str(new_date)
			# list = list + "<a href='delete?id="+data['name']+"&cn="+container['name']+"'>Delete</a><br>"
	# return '''<!DOCTYPE html>
# <html>

  # <head>
    # <title>Python Flask Application</title>
    # <meta charset="utf-8">
    # <meta http-equiv="X-UA-Compatible" content="IE=edge">
    # <meta name="viewport" content="width=device-width, initial-scale=1">
    # <link rel="stylesheet" href="static/stylesheets/style.css">
  # </head>

  # <body>''' + list + '''
    
  # </body>

# </html>'''

@app.route('/list', methods=['POST','GET'])
def list():
	if request.method == 'GET':			
		db = MySQLdb.connect("us-cdbr-iron-east-04.cleardb.net","bb502b604c0f43","d302d795","ad_a09e2e841ca1aaf")
		cursor = db.cursor()
		
		sql = "select id from files"
		cursor.execute(sql)
		results = cursor.fetchall()
		
		list = ''
		if cursor.rowcount>0:
			for row in results:
				list = list + "<a href='download?id="+row[0]+"'>"+row[0]+"</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
				list = list + "<a href='delete?id="+row[0]+"'>Delete</a><br>"
		return '''<!DOCTYPE html>
	<html>

	  <head>
		<title>Python Flask Application</title>
		<meta charset="utf-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge">
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<link rel="stylesheet" href="static/stylesheets/style.css">
	  </head>

	  <body>''' + list + '''
		
	  </body>

	</html>'''


@app.route('/download', methods=['GET'])
def download():
	if request.method == 'GET':
		id = request.args.get('id')
		container_name = request.args.get('cn')
		document = conn.get_object(container_name, id)
		
		if id[:2]=='e_':
			#plain_text = cipher_suite.decrypt(ef[1])
			response = make_response(cipher_suite.decrypt(document[1]))
		else:
			#response = make_response(str(gpg.decrypt(document[1], passphrase=ukey)))
			response = make_response(document[1])
		
		response.headers["Content-Disposition"] = "attachment; filename="+id
		return response

@app.route('/delete', methods=['GET'])
def delete():
	if request.method == 'GET':
		id = request.args.get('id')
		container_name = request.args.get('cn')
		conn.delete_object(container_name, id)
		#return 'File was deleted successfully.'
		return redirect(url_for('list'))


#port = os.getenv('VCAP_APP_PORT', '5000')
port = int(os.getenv('VCAP_APP_PORT', 8080))
if __name__ == "__main__":
	#app.run(debug=True)
	app.run(host='0.0.0.0',port=port)