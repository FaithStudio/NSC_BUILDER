import aes128
import Print
import os
import shutil
import json
from Fs import Nsp as squirrelNSP
from Fs import Xci as squirrelXCI
from Fs.Nca import NcaHeader
from Fs.File import MemoryFile
import sq_tools
import io
from Fs import Type as FsType
from Fs import factory
import Keys
from binascii import hexlify as hx, unhexlify as uhx
from DBmodule import Exchange as exchangefile
import math
import sys
import subprocess
from mtp.wpd import is_switch_connected
import listmanager
import csv
from colorama import Fore, Back, Style
import time
from secondary import clear_Screen
from python_pick import pick
from python_pick import Picker
from Drive import Private as DrivePrivate
from Drive import Public as DrivePublic
from Drive import DriveTools
import requests
from Drive import Download as Drv
from Interface import About
from workers import concurrent_scrapper
from mtpinstaller import get_storage_info
try:
	import ujson as json
except:
	import json

if not is_switch_connected():
	sys.exit("Switch device isn't connected.\nCheck if mtp responder is running!!!")	
	
bucketsize = 81920

# SET ENVIRONMENT
squirrel_dir=os.path.abspath(os.curdir)
NSCB_dir=os.path.abspath('../'+(os.curdir))

if os.path.exists(os.path.join(squirrel_dir,'ztools')):
	NSCB_dir=squirrel_dir
	zconfig_dir=os.path.join(NSCB_dir, 'zconfig')	  
	ztools_dir=os.path.join(NSCB_dir,'ztools')
	squirrel_dir=ztools_dir
elif os.path.exists(os.path.join(NSCB_dir,'ztools')):
	squirrel_dir=squirrel_dir
	ztools_dir=os.path.join(NSCB_dir, 'ztools')
	zconfig_dir=os.path.join(NSCB_dir, 'zconfig')
else:	
	ztools_dir=os.path.join(NSCB_dir, 'ztools')
	zconfig_dir=os.path.join(NSCB_dir, 'zconfig')

testroute1=os.path.join(squirrel_dir, "squirrel.py")
testroute2=os.path.join(squirrel_dir, "squirrel.exe")
urlconfig=os.path.join(zconfig_dir,'NUT_DB_URL.txt')
isExe=False
if os.path.exists(testroute1):
	squirrel=testroute1
	isExe=False
elif os.path.exists(testroute2):	
	squirrel=testroute2
	isExe=True
bin_folder=os.path.join(ztools_dir, 'bin')
nscb_mtp=os.path.join(bin_folder, 'nscb_mtp.exe')
cachefolder=os.path.join(ztools_dir, '_mtp_cache_')
if not os.path.exists(cachefolder):
	os.makedirs(cachefolder)
games_installed_cache=os.path.join(cachefolder, 'games_installed.txt')
mtp_source_lib=os.path.join(zconfig_dir,'mtp_source_libraries.txt')
mtp_internal_lib=os.path.join(zconfig_dir,'mtp_SD_libraries.txt')
storage_info=os.path.join(cachefolder, 'storage.csv')
download_lib_file = os.path.join(zconfig_dir, 'mtp_download_libraries.txt')
remote_lib_file = os.path.join(zconfig_dir, 'remote_libraries.txt')
cache_lib_file= os.path.join(zconfig_dir, 'remote_cache_location.txt')
_1fichier_token=os.path.join((os.path.join(zconfig_dir, 'credentials')),'_1fichier_token.tk')
remote_lib_cache=os.path.join(zconfig_dir, 'remote_lib_cache')	

def libraries(tfile):
	db={}
	try:
		with open(tfile,'rt',encoding='utf8') as csvfile:
			readCSV = csv.reader(csvfile, delimiter='|')	
			i=0	
			for row in readCSV:
				if i==0:
					csvheader=row
					i=1
				else:
					dict_={}
					for j in range(len(csvheader)):
						try:
							if row[j]==None or row[j]=='':
								dict_[csvheader[j]]=None
							else:	
								dict_[csvheader[j]]=row[j]
						except:
							dict_[csvheader[j]]=None
					db[row[0]]=dict_
		return db			
	except BaseException as e:
		Print.error('Exception: ' + str(e))
		return False
	
def get_cache_lib():
	db=libraries(cache_lib_file)
	TD=None;lib=None;path="null";libpath=None
	for entry in db:
		path=db[entry]['path']
		TD=db[entry]['TD_name']
		lib=entry
		libpath=path
		break
	if TD=='':
		TD=None
	return lib,TD,libpath		
	
def addtodrive(filename,truecopy=True):
	if os.path.exists(cache_lib_file):
		lib,TD,libpath=get_cache_lib()
		if lib!=None:
			file_id, is_download_link=DrivePublic.parse_url(filename)		
			if is_download_link:
				remote=DrivePrivate.location(route=libpath,TD_Name=TD)		
				result=remote.drive_service.files().get(fileId=file_id, fields="name,mimeType").execute()		
				name=result['name']	
				testpath=('{}/{}').format(libpath,name)
				remote=DrivePrivate.location(route=testpath,TD_Name=TD)	
				if remote.name==None:			
					name=DrivePrivate.add_to_drive(url=filename,filepath=libpath,makecopy=truecopy,TD=TD)
					filename=('{}/{}').format(libpath,name)
					ID,name,type,size,md5,remote=DrivePrivate.get_Data(filename,TD=TD,Print=False)
				else:
					filename=testpath
				globalremote=remote
		return filename	

def interface_filter(path=None):
	title = 'Add a search filter?: '
	options = ['Yes','No']	
	selected = pick(options, title, min_selection_count=1)
	response=selected[0]
	if response=='No':
		return None
	else:
		clear_Screen()
		About()
		if path != None:
			print("Filepath {}\n".format(str(path)))
		ck=input('INPUT SEARCH FILTER: ')
		return ck		

def pick_order():
	title = 'Select order to list the files: \n + Press enter or intro to select \n + Press E to scape back to menu'
	db=libraries(download_lib_file)
	options = ['name_ascending','name_descending','size_ascending','size_descending','date_ascending','date_descending']
	picker = Picker(options, title, min_selection_count=1)	
	def end_selection(picker):
		return False,-1	
	picker.register_custom_handler(ord('e'),  end_selection)
	picker.register_custom_handler(ord('E'),  end_selection)		
	selected = picker.start()	
	if selected[0]==False:
		return False
	order=selected[0]
	return order		

def interface_filter_local(filelist):
	title = 'Add a search filter?: '
	options = ['Yes','No']	
	selected = pick(options, title, min_selection_count=1)
	response=selected[0]
	if response=='No':
		return filelist
	else:
		clear_Screen()
		About()
		ck=input('INPUT SEARCH FILTER: ')
		filelist=listmanager.filter_vlist(filelist,token=ck,Print=False)
	return filelist	
	
def eval_link(link,tfile,userfile):	
	link=input("Enter your choice: ")
	link=link.strip()
	if '&' in link:
		varout='999'
	elif len(link)<2:
		varout=link
	else:
		varout='999'
	with open(userfile,"w", encoding='utf8') as userinput:
		userinput.write(varout)		
	if link.startswith('https://1fichier.com'):
		with open(tfile,"a", encoding='utf8') as textfile:
			textfile.write(link+'\n')				
	elif link.startswith('https://drive.google.com'):
		with open(tfile,"a", encoding='utf8') as textfile:
			textfile.write(link+'\n')	

def select_from_libraries(tfile):	
	db=libraries(remote_lib_file)
	if db==False:
		sys.exit(f"Missing {remote_lib_file}")
	paths,TDs=Drv.pick_libraries()
	if paths==False:
		return False	
	filter=interface_filter()	
	order=pick_order()
	if order==False:
		return False
	print("  * Parsing files from Google Drive. Please Wait...")		
	if isinstance(paths, list):
		db={}
		for i in range(len(paths)):
			db[paths[i]]={'path':paths[i],'TD_name':TDs[i]}		
		files=concurrent_scrapper(filter=filter,order=order,remotelib='all',db=db)
	else:
		db={}
		db[paths]={'path':paths,'TD_name':TDs}			
		files=concurrent_scrapper(filter=filter,order=order,remotelib='all',db=db)	
	print("  * Entering File Picker")	
	title = 'Select content to install or transfer: \n + Press space or right to select content \n + Press E to finish selection'
	filenames=[]
	for f in files:
		filenames.append(f[0])
	options=filenames
	picker = Picker(options, title, multi_select=True, min_selection_count=1)
	def end_selection(picker):
		return False,-1
	picker.register_custom_handler(ord('e'),  end_selection);picker.register_custom_handler(ord('E'),  end_selection)
	selected=picker.start()
	if selected[0]==False:
		print("    User didn't select any files")
		return False
	with open(tfile,'a') as  textfile:		
		for f in selected:
			textfile.write((files[f[1]])[2]+'/'+(files[f[1]])[0]+'\n')

def select_from_cache(tfile):	
	cache_is_setup=False
	if not os.path.exists(remote_lib_cache):
		os.makedirs(remote_lib_cache)
	jsonlist=listmanager.folder_to_list(remote_lib_cache,extlist=['json'])	
	if not jsonlist:
		print("Cache wasn't found. Generating cache up...")
		from workers import concurrent_cache
		concurrent_cache()
	jsonlist=listmanager.folder_to_list(remote_lib_cache,extlist=['json'])			
	if not jsonlist:
		sys.exit("Can't setup remote cache. Are libraries set up?")
	libnames=[]
	for j in jsonlist:
		bname=os.path.basename(j) 
		bname=bname.replace('.json','')
		libnames.append(bname)
	title = 'Select libraries to search:  \n + Press space or right to select content \n + Press E to finish selection \n + Press A to select all libraries'
	db=libraries(remote_lib_file)
	options = libnames
	picker = Picker(options, title,multi_select=True,min_selection_count=1)	
	def end_selection(picker):
		return False,-1	
	def select_all(picker):
		return True,libnames
	picker.register_custom_handler(ord('e'),  end_selection)
	picker.register_custom_handler(ord('E'),  end_selection)	
	picker.register_custom_handler(ord('a'),  select_all)
	picker.register_custom_handler(ord('A'),  select_all)	
	selected = picker.start()	
	if selected[0]==False:
		print("User didn't select any libraries")
		return False,False		
	if selected[0]==True:	
		cachefiles=jsonlist
	else:
		cachefiles=[]
		for entry in selected:
			fname=entry[0]+'.json'
			fpath=os.path.join(remote_lib_cache,fname)
			cachefiles.append(fpath)
	cachedict={}
	for cach in cachefiles:
		with open(cach) as json_file:					
			data = json.load(json_file)		
		for entry in data:
			if not entry in cachedict:
				cachedict[entry]=data[entry]
	# for k in cachedict.keys():
		# print(k)
	order=pick_order()
	if order==False:
		return False	
	options=[]	
	if order=='name_ascending':
		options=sorted(cachedict,key=lambda x:cachedict[x]['filepath'])
	elif order=='name_descending':	
		options=sorted(cachedict,key=lambda x:cachedict[x]['filepath'])
		options.reverse()
	elif order=='size_ascending':
		options=sorted(cachedict,key=lambda x:cachedict[x]['size'])
	elif order=='size_descending':	
		options=sorted(cachedict,key=lambda x:cachedict[x]['size'])
		options.reverse()	
	elif order=='date_ascending':
		options=sorted(cachedict,key=lambda x:cachedict[x]['date'])
	elif order=='date_descending':	
		options=sorted(cachedict,key=lambda x:cachedict[x]['date'])
		options.reverse()	
	options=interface_filter_local(options)	
	print("  * Entering File Picker")	
	title = 'Select content to install or transfer: \n + Press space or right to select content \n + Press E to finish selection'
	picker = Picker(options, title, multi_select=True, min_selection_count=1)
	def end_selection(picker):
		return False,-1
	picker.register_custom_handler(ord('e'),  end_selection);picker.register_custom_handler(ord('E'),  end_selection)
	selected=picker.start()
	if selected[0]==False:
		print("    User didn't select any files")
		return False
	with open(tfile,'a') as  textfile:		
		for f in selected:
			fpath=(cachedict[f[0]])['filepath']
			textfile.write(fpath+'\n')
			

def loop_install(tfile,destiny="SD",outfolder=None,ch_medium=True,check_fw=True,patch_keygen=False,ch_base=False,ch_other=False,truecopy=True,checked=False):	
	if not os.path.exists(tfile):
		sys.exit(f"Couldn't find {tfile}")	
	from mtpinstaller import retrieve_installed,parsedinstalled
	installed=[]
	if ch_base==True or ch_other==True:
		if checked==False:		
			print("Content check activated")			
			retrieve_installed()
			installed=parsedinstalled()		
		elif checked==True:
			print("Content check activated. Games are preparsed")		
			installed=parsedinstalled()		
	file_list=listmanager.read_lines_to_list(tfile,all=True)	
	for item in file_list:
		if item.startswith('https://1fichier.com'):
			print("Item is 1fichier link. Redirecting...")
			fichier_install(item,destiny,ch_medium,ch_base=ch_base,ch_other=ch_other,installed_list=installed)			
		elif item.startswith('https://drive.google.com'):
			print("Item is google drive public link. Redirecting...")
			public_gdrive_install(item,destiny,outfolder=outfolder,ch_medium=ch_medium,check_fw=check_fw,patch_keygen=patch_keygen,ch_base=ch_base,ch_other=ch_other,checked=checked,truecopy=truecopy,installed_list=installed)			
		elif os.path.exists(item):
			print("Item is a local link. Skipping...")	
		else:
			test=item.split('|')
			item=test[0]
			lib,TD,libpath=get_library_from_path(remote_lib_file,item)			
			if lib!=None:
				print("Item is a remote library link. Redirecting...")
				gdrive_install(item,destiny,outfolder=outfolder,ch_medium=ch_medium,check_fw=check_fw,patch_keygen=patch_keygen,ch_base=ch_base,ch_other=ch_other,checked=checked,installed_list=installed)
			else:
				print("Couldn't find file. Skipping...")
	
def get_library_from_path(tfile=None,filename=None):
	if tfile==None:
		db=libraries(remote_lib_file)
	else:
		db=libraries(tfile)		
	TD=None;lib=None;path="null"
	for entry in db:
		path=db[entry]['path']
		if filename.startswith(path):
			TD=db[entry]['TD_name']
			lib=entry
			libpath=path
			break
		else:
			pass
	if lib==None:
		db=libraries(cache_lib_file)
		TD=None;lib=None;path="null"
		for entry in db:
			path=db[entry]['path']
			if filename.startswith(path):
				TD=db[entry]['TD_name']
				lib=entry
				libpath=path
				break
			else:
				pass		
	if TD=='':
		TD=None			
	return lib,TD,libpath	
	
def gdrive_install(filename,destiny="SD",outfolder=None,ch_medium=True,check_fw=True,patch_keygen=False,ch_base=False,ch_other=False,checked=False,installed_list=False):
	lib,TD,libpath=get_library_from_path(remote_lib_file,filename)
	ID,name,type,size,md5,remote=DrivePrivate.get_Data(filename,TD=TD,Print=False)
	# header=DrivePrivate.get_html_header(remote.access_token)
	token=remote.access_token
	name=remote.name
	sz=remote.size
	URL='https://www.googleapis.com/drive/v3/files/'+remote.ID+'?alt=media'	
	ext=name.split('.')
	ext=ext[-1]
	if not name.endswith('nsp') and not name.endswith('nsz'):
		sys.exit(f"Extension not supported for direct instalation {ext} in {name}")	
	print("- Retrieving Space on device")
	SD_ds,SD_fs,NAND_ds,NAND_fs,FW,device=get_storage_info()
	print("- Calculating Installed size")	
	filesize=int(sz)
	if destiny=="SD":
		print(f"  * SD free space: {SD_fs} ({sq_tools.getSize(SD_fs)})")	
		print(f"  * File size: {filesize} ({sq_tools.getSize(filesize)})")		
		if filesize>SD_fs:
			if filesize<NAND_fs and ch_medium==True:
				print("  Not enough space on SD. Changing target to EMMC")
				print(f"  * EMMC free space: {NAND_fs} ({sq_tools.getSize(NAND_fs)})")						
				destiny="NAND"
			elif  ch_medium==False:	
				sys.exit("   NOT ENOUGH SPACE SD STORAGE")				
			else:
				sys.exit("   NOT ENOUGH SPACE ON DEVICE")				
	else:
		print(f"  * EMMC free space: {NAND_fs} ({sq_tools.getSize(NAND_fs)})")	
		print(f"  * File size: {filesize} ({sq_tools.getSize(filesize)})")		
		if filesize>NAND_fs:		
			if filesize<SD_fs and ch_medium==True:
				print("  Not enough space on EMMC. Changing target to SD")			
				print(f"  * SD free space: {SD_fs} ({sq_tools.getSize(SD_fs)})")					
				destiny="SD"
			elif  ch_medium==False:	
				sys.exit("   NOT ENOUGH SPACE EMMC STORAGE")							
			else:
				sys.exit("   NOT ENOUGH SPACE ON DEVICE")
	kgwarning=False			
	if check_fw==True:	
		cnmtdata,files_list,remote=DriveTools.get_cnmt_data(file=remote)		
		keygeneration=int(cnmtdata['keygeneration'])
		if FW!='unknown':	
			try:
				FW_RSV,RRSV=sq_tools.transform_fw_string(FW)
				FW_kg=sq_tools.kg_by_RSV(FW_RSV)
			except BaseException as e:
				Print.error('Exception: ' + str(e))
				FW='unknown'
				FW_kg='unknown'
				pass
		if FW!='unknown' and FW_kg!='unknown':			
			if int(keygeneration)>int(FW_kg):
				kgwarning=True
				tgkg=int(FW_kg)
			else:
				tgkg=keygeneration
		else:
			tgkg=keygeneration
		print(f"- Console Firmware: {FW} ({FW_RSV}) - keygen {FW_kg})")		
		print(f"- File keygeneration: {keygeneration}")				
		if kgwarning==True:
			print("File requires a higher firmware. Skipping...")
			return False	
	if installed_list!=False:
		fileid,fileversion,cctag,nG,nU,nD,baseid=listmanager.parsetags(name)
		fileversion=int(fileversion)
		if fileid.endswith('000') and fileversion==0 and fileid in installed_list.keys() and ch_base==True:
			print("Base game already installed. Skipping...")
			return False	
		elif fileid.endswith('000') and fileid in installed_list.keys() and ch_other==True:
			updid=fileid[:-3]+'800'
			if fileversion>((installed_list[fileid])[2]):
				print("Asking DBI to delete previous content")
				process=subprocess.Popen([nscb_mtp,"DeleteID","-ID",fileid])	
				while process.poll()==None:
					if process.poll()!=None:
						process.terminate();					
				process=subprocess.Popen([nscb_mtp,"DeleteID","-ID",updid])		
				while process.poll()==None:
					if process.poll()!=None:
						process.terminate();					
			else:
				print("The update is a previous version than the installed on device.Skipping..")
				listmanager.striplines(tfile,counter=True)
				return False		
		elif ch_other==True	and fileid in installed_list.keys():
			if fileversion>((installed_list[fileid])[2]):
				print("Asking DBI to delete previous update")
				process=subprocess.Popen([nscb_mtp,"DeleteID","-ID",fileid])					
				while process.poll()==None:
					if process.poll()!=None:
						process.terminate();
			else:
				print("The update is a previous version than the installed on device.Skipping..")
				listmanager.striplines(tfile,counter=True)
				return False						
	process=subprocess.Popen([nscb_mtp,"DriveInstall","-ori",URL,"-dst",destiny,"-name",name,"-size",sz,"-tk",token])
	while process.poll()==None:
		if process.poll()!=None:
			process.terminate();	

def public_gdrive_install(filepath,destiny="SD",truecopy=True,outfolder=None,ch_medium=True,check_fw=True,patch_keygen=False,ch_base=False,ch_other=False,installed_list=False):
	lib,TD,libpath=get_cache_lib()
	if lib==None:
		sys.exit(f"Google Drive Public Links are only supported via cache folder")	
	filename=addtodrive(filepath,truecopy=truecopy)
	ID,name,type,size,md5,remote=DrivePrivate.get_Data(filename,TD=TD,Print=False)	
	token=remote.access_token
	name=remote.name
	sz=remote.size
	URL='https://www.googleapis.com/drive/v3/files/'+remote.ID+'?alt=media'	
	ext=name.split('.')
	ext=ext[-1]
	if not name.endswith('nsp') and not name.endswith('nsz'):
		sys.exit(f"Extension not supported for direct instalation {ext} in {name}")
	print("- Retrieving Space on device")
	SD_ds,SD_fs,NAND_ds,NAND_fs,FW,device=get_storage_info()
	print("- Calculating Installed size")	
	filesize=int(sz)
	if destiny=="SD":
		print(f"  * SD free space: {SD_fs} ({sq_tools.getSize(SD_fs)})")	
		print(f"  * File size: {filesize} ({sq_tools.getSize(filesize)})")		
		if filesize>SD_fs:
			if filesize<NAND_fs and ch_medium==True:
				print("  Not enough space on SD. Changing target to EMMC")
				print(f"  * EMMC free space: {NAND_fs} ({sq_tools.getSize(NAND_fs)})")						
				destiny="NAND"
			elif  ch_medium==False:	
				sys.exit("   NOT ENOUGH SPACE SD STORAGE")				
			else:
				sys.exit("   NOT ENOUGH SPACE ON DEVICE")				
	else:
		print(f"  * EMMC free space: {NAND_fs} ({sq_tools.getSize(NAND_fs)})")	
		print(f"  * File size: {filesize} ({sq_tools.getSize(filesize)})")		
		if filesize>NAND_fs:		
			if filesize<SD_fs and ch_medium==True:
				print("  Not enough space on EMMC. Changing target to SD")			
				print(f"  * SD free space: {SD_fs} ({sq_tools.getSize(SD_fs)})")					
				destiny="SD"
			elif  ch_medium==False:	
				sys.exit("   NOT ENOUGH SPACE EMMC STORAGE")							
			else:
				sys.exit("   NOT ENOUGH SPACE ON DEVICE")
	kgwarning=False						
	if check_fw==True:	
		cnmtdata,files_list,remote=DriveTools.get_cnmt_data(file=remote)		
		keygeneration=int(cnmtdata['keygeneration'])
		if FW!='unknown':	
			try:
				FW_RSV,RRSV=sq_tools.transform_fw_string(FW)
				FW_kg=sq_tools.kg_by_RSV(FW_RSV)
			except BaseException as e:
				Print.error('Exception: ' + str(e))
				FW='unknown'
				FW_kg='unknown'
				pass
		if FW!='unknown' and FW_kg!='unknown':			
			if int(keygeneration)>int(FW_kg):
				kgwarning=True
				tgkg=int(FW_kg)
			else:
				tgkg=keygeneration
		else:
			tgkg=keygeneration
		print(f"- Console Firmware: {FW} ({FW_RSV}) - keygen {FW_kg})")		
		print(f"- File keygeneration: {keygeneration}")				
		if kgwarning==True:
			print("File requires a higher firmware. Skipping...")
			return False		
	if installed_list!=False:
		fileid,fileversion,cctag,nG,nU,nD,baseid=listmanager.parsetags(name)
		fileversion=int(fileversion)
		if fileid.endswith('000') and fileversion==0 and fileid in installed_list.keys() and ch_base==True:
			print("Base game already installed. Skipping...")
			return False	
		elif fileid.endswith('000') and fileid in installed_list.keys() and ch_other==True:
			updid=fileid[:-3]+'800'
			if fileversion>((installed_list[fileid])[2]):
				print("Asking DBI to delete previous content")
				process=subprocess.Popen([nscb_mtp,"DeleteID","-ID",fileid])	
				while process.poll()==None:
					if process.poll()!=None:
						process.terminate();					
				process=subprocess.Popen([nscb_mtp,"DeleteID","-ID",updid])		
				while process.poll()==None:
					if process.poll()!=None:
						process.terminate();					
			else:
				print("The update is a previous version than the installed on device.Skipping..")
				listmanager.striplines(tfile,counter=True)
				return False		
		elif ch_other==True	and fileid in installed_list.keys():
			if fileversion>((installed_list[fileid])[2]):
				print("Asking DBI to delete previous update")
				process=subprocess.Popen([nscb_mtp,"DeleteID","-ID",fileid])					
				while process.poll()==None:
					if process.poll()!=None:
						process.terminate();
			else:
				print("The update is a previous version than the installed on device.Skipping..")
				listmanager.striplines(tfile,counter=True)
				return False			
	process=subprocess.Popen([nscb_mtp,"DriveInstall","-ori",URL,"-dst",destiny,"-name",name,"-size",sz,"-tk",token])
	while process.poll()==None:
		if process.poll()!=None:
			process.terminate();		
	
def fichier_install(url,destiny="SD",ch_medium=True,ch_base=False,ch_other=False,installed_list=False):
	if not os.path.exists(_1fichier_token):
		sys.exit("No 1fichier token setup")
	with open(_1fichier_token,'rt',encoding='utf8') as tfile:
		token=(tfile.readline().strip())
	if token==None:
		sys.exit("Missing 1fichier token")		
	APIkey=token
	auth={'Authorization':f'Bearer {APIkey}','Content-Type':'application/json'}
	session = requests.session()
	download_params = {
		'url' : url,
		'inline' : 0,
		'cdn' : 0,
		'restrict_ip':  0,
		'no_ssl' : 0,
	}			
	info_params={
		'url' : url	
	}
	r=session.post('https://api.1fichier.com/v1/file/info.cgi',json=info_params,headers=auth)
	info_dict=r.json()
	# print(info_dict)
	sz=info_dict['size']
	name=info_dict['filename']
	r=session.post('https://api.1fichier.com/v1/download/get_token.cgi',json=download_params,headers=auth)
	dict_=r.json()
	# print(dict_)
	ext=name.split('.')
	ext=ext[-1]
	if not name.endswith('nsp') and not name.endswith('nsz'):
		sys.exit(f"Extension not supported for direct instalation {ext} in {name}")			
	if not dict_['status']=="OK":
		sys.exit(f"API call returned {dict_['status']}")			
	URL=dict_['url']
	print("- Retrieving Space on device")
	SD_ds,SD_fs,NAND_ds,NAND_fs,FW,device=get_storage_info()
	print("- Calculating Installed size")	
	filesize=int(sz)
	if destiny=="SD":
		print(f"  * SD free space: {SD_fs} ({sq_tools.getSize(SD_fs)})")	
		print(f"  * File size: {filesize} ({sq_tools.getSize(filesize)})")		
		if filesize>SD_fs:
			if filesize<NAND_fs and ch_medium==True:
				print("  Not enough space on SD. Changing target to EMMC")
				print(f"  * EMMC free space: {NAND_fs} ({sq_tools.getSize(NAND_fs)})")						
				destiny="NAND"
			elif  ch_medium==False:	
				sys.exit("   NOT ENOUGH SPACE SD STORAGE")				
			else:
				sys.exit("   NOT ENOUGH SPACE ON DEVICE")				
	else:
		print(f"  * EMMC free space: {NAND_fs} ({sq_tools.getSize(NAND_fs)})")	
		print(f"  * File size: {filesize} ({sq_tools.getSize(filesize)})")		
		if filesize>NAND_fs:		
			if filesize<SD_fs and ch_medium==True:
				print("  Not enough space on EMMC. Changing target to SD")			
				print(f"  * SD free space: {SD_fs} ({sq_tools.getSize(SD_fs)})")					
				destiny="SD"
			elif  ch_medium==False:	
				sys.exit("   NOT ENOUGH SPACE EMMC STORAGE")							
			else:
				sys.exit("   NOT ENOUGH SPACE ON DEVICE")			
	if installed_list!=False:
		fileid,fileversion,cctag,nG,nU,nD,baseid=listmanager.parsetags(name)
		fileversion=int(fileversion)
		if fileid.endswith('000') and fileversion==0 and fileid in installed_list.keys() and ch_base==True:
			print("Base game already installed. Skipping...")
			return False	
		elif fileid.endswith('000') and fileid in installed_list.keys() and ch_other==True:
			updid=fileid[:-3]+'800'
			if fileversion>((installed_list[fileid])[2]):
				print("Asking DBI to delete previous content")
				process=subprocess.Popen([nscb_mtp,"DeleteID","-ID",fileid])	
				while process.poll()==None:
					if process.poll()!=None:
						process.terminate();					
				process=subprocess.Popen([nscb_mtp,"DeleteID","-ID",updid])		
				while process.poll()==None:
					if process.poll()!=None:
						process.terminate();					
			else:
				print("The update is a previous version than the installed on device.Skipping..")
				listmanager.striplines(tfile,counter=True)
				return False		
		elif ch_other==True	and fileid in installed_list.keys():
			if fileversion>((installed_list[fileid])[2]):
				print("Asking DBI to delete previous update")
				process=subprocess.Popen([nscb_mtp,"DeleteID","-ID",fileid])					
				while process.poll()==None:
					if process.poll()!=None:
						process.terminate();
			else:
				print("The update is a previous version than the installed on device.Skipping..")
				listmanager.striplines(tfile,counter=True)
				return False				
	process=subprocess.Popen([nscb_mtp,"fichierInstall","-ori",URL,"-dst",destiny,"-name",name,"-size",str(sz)])
	while process.poll()==None:
		if process.poll()!=None:
			process.terminate();		
			
def gdrive_transfer(filename,destiny="SD"):
	if destiny=="SD":
		destiny="1: External SD Card/"
	lib,TD,libpath=get_library_from_path(remote_lib_file,filename)
	ID,name,type,size,md5,remote=DrivePrivate.get_Data(filename,TD=TD,Print=False)
	# header=DrivePrivate.get_html_header(remote.access_token)
	token=remote.access_token
	name=remote.name
	sz=remote.size
	URL='https://www.googleapis.com/drive/v3/files/'+remote.ID+'?alt=media'	
	ext=name.split('.')
	ext=ext[-1]
	file_size=int(sz)	
	print("- Retrieving Space on device")
	SD_ds,SD_fs,NAND_ds,NAND_fs,FW,device=get_storage_info()
	print(f"  * SD free space: {SD_fs} ({sq_tools.getSize(SD_fs)})")	
	print(f"  * File installed size: {file_size} ({sq_tools.getSize(file_size)})")		
	if file_size>SD_fs:
		print("  Not enough space on SD. Changing target to EMMC")
		print(f"  * EMMC free space: {NAND_fs} ({sq_tools.getSize(NAND_fs)})")						
		sys.exit("   NOT ENOUGH SPACE SD STORAGE")		
	process=subprocess.Popen([nscb_mtp,"DriveTransfer","-ori",URL,"-dst",destiny,"-name",name,"-size",sz,"-tk",token])
	while process.poll()==None:
		if process.poll()!=None:
			process.terminate();	

def public_gdrive_transfer(filepath,destiny="SD",truecopy=True):
	lib,TD,libpath=get_cache_lib()
	if lib==None:
		sys.exit(f"Google Drive Public Links are only supported via cache folder")	
	if destiny=="SD":
		destiny="1: External SD Card/"		
	filename=addtodrive(filepath,truecopy=truecopy)
	ID,name,type,size,md5,remote=DrivePrivate.get_Data(filename,TD=TD,Print=False)	
	token=remote.access_token
	name=remote.name
	sz=remote.size
	URL='https://www.googleapis.com/drive/v3/files/'+remote.ID+'?alt=media'	
	ext=name.split('.')
	ext=ext[-1]		
	file_size=int(sz)
	print("- Retrieving Space on device")
	SD_ds,SD_fs,NAND_ds,NAND_fs,FW,device=get_storage_info()	
	print(f"  * SD free space: {SD_fs} ({sq_tools.getSize(SD_fs)})")	
	print(f"  * File installed size: {file_size} ({sq_tools.getSize(file_size)})")		
	if file_size>SD_fs:
		print("  Not enough space on SD. Changing target to EMMC")
		print(f"  * EMMC free space: {NAND_fs} ({sq_tools.getSize(NAND_fs)})")						
		sys.exit("   NOT ENOUGH SPACE SD STORAGE")		
	process=subprocess.Popen([nscb_mtp,"DriveTransfer","-ori",URL,"-dst",destiny,"-name",name,"-size",sz,"-tk",token])
	while process.poll()==None:
		if process.poll()!=None:
			process.terminate();		
	
def fichier_transfer(url,destiny="SD"):
	if not os.path.exists(_1fichier_token):
		sys.exit("No 1fichier token setup")
	with open(_1fichier_token,'rt',encoding='utf8') as tfile:
		token=(tfile.readline().strip())
	if token==None:
		sys.exit("Missing 1fichier token")		
	APIkey=token
	auth={'Authorization':f'Bearer {APIkey}','Content-Type':'application/json'}
	session = requests.session()
	download_params = {
		'url' : url,
		'inline' : 0,
		'cdn' : 0,
		'restrict_ip':  0,
		'no_ssl' : 0,
	}			
	info_params={
		'url' : url	
	}
	r=session.post('https://api.1fichier.com/v1/file/info.cgi',json=info_params,headers=auth)
	info_dict=r.json()
	# print(info_dict)
	sz=info_dict['size']
	name=info_dict['filename']
	r=session.post('https://api.1fichier.com/v1/download/get_token.cgi',json=download_params,headers=auth)
	dict_=r.json()
	# print(dict_)
	ext=name.split('.')
	ext=ext[-1]			
	if not dict_['status']=="OK":
		sys.exit(f"API call returned {dict_['status']}")			
	URL=dict_['url']
	print("- Retrieving Space on device")
	SD_ds,SD_fs,NAND_ds,NAND_fs,FW,device=get_storage_info()
	print("- Calculating File size")	
	file_size=int(sz)
	print(f"  * SD free space: {SD_fs} ({sq_tools.getSize(SD_fs)})")	
	print(f"  * File installed size: {file_size} ({sq_tools.getSize(file_size)})")		
	if file_size>SD_fs:
		print("  Not enough space on SD. Changing target to EMMC")
		print(f"  * EMMC free space: {NAND_fs} ({sq_tools.getSize(NAND_fs)})")						
		sys.exit("   NOT ENOUGH SPACE SD STORAGE")	
	process=subprocess.Popen([nscb_mtp,"fichierTransfer","-ori",URL,"-dst",destiny,"-name",name,"-size",str(sz)])
	while process.poll()==None:
		if process.poll()!=None:
			process.terminate();

def loop_transfer(tfile):	
	if not os.path.exists(tfile):
		sys.exit(f"Couldn't find {tfile}")		
	from mtp_game_manager import pick_transfer_folder
	destiny=pick_transfer_folder()
	file_list=listmanager.read_lines_to_list(tfile,all=True)	
	for item in file_list:
		if item.startswith('https://1fichier.com'):
			print("Item is 1fichier link. Redirecting...")
			fichier_transfer(item,destiny)			
		elif item.startswith('https://drive.google.com'):
			print("Item is google drive public link. Redirecting...")
			public_gdrive_transfer(item,destiny)			
		elif os.path.exists(item):
			print("Item is a local link. Skipping...")	
		else:
			test=item.split('|')
			item=test[0]
			lib,TD,libpath=get_library_from_path(remote_lib_file,item)			
			if lib!=None:
				print("Item is a remote library link. Redirecting...")
				gdrive_transfer(item,destiny)
				

def get_libs_remote_source(lib=remote_lib_file):
	libraries={}
	libtfile=lib
	with open(libtfile,'rt',encoding='utf8') as csvfile:
		readCSV = csv.reader(csvfile, delimiter='|')	
		i=0;up=False;tdn=False;	
		for row in readCSV:
			if i==0:
				csvheader=row
				i=1
				if 'library_name' and 'path' and 'TD_name' and 'Update' in csvheader:
					lb=csvheader.index('library_name')
					pth=csvheader.index('path')	
					tdn=csvheader.index('TD_name')	
					up=csvheader.index('Update')	
				else:
					if 'library_name' and 'path' and 'TD_name' in csvheader:
						lb=csvheader.index('library_name')
						tdn=csvheader.index('TD_name')
						pth=csvheader.index('path')				
					else:break	
			else:	
				try:
					update=False
					library=str(row[lb])
					route=str(row[pth])		
					if tdn!=False:
						try:
							TD=str(row[tdn])
							if TD=='':
								TD=None
						except:
							TD=None
					else:	
						TD=None					
					if up!=False:
						try:
							update=str(row[up])
							if update.upper()=="TRUE":
								update=True
							else:
								update=False
						except:	
							update=True
					else:
						update=False
					libraries[library]=[route,TD,update]
				except BaseException as e:
					Print.error('Exception: ' + str(e))			
					pass
		if not libraries:
			return False
	return libraries				

def update_console_from_gd(libraries="all",destiny="SD",exclude_xci=True,prioritize_nsz=True,tfile=None,verification=True,ch_medium=True,ch_other=False,autoupd_aut=True):	
	if tfile==None:
		tfile=os.path.join(NSCB_dir, 'MTP1.txt')
	if os.path.exists(tfile):
		try:
			os.remove(tfile)
		except: pass			
	libdict=get_libs_remote_source(remote_lib_file);
	if libdict==False:
		sys.exit("No libraries set up")
	pths={};TDs={};
	if libraries=="all":
		for entry in libdict.keys():
			pths[entry]=((libdict[entry])[0])
			TDs[entry]=((libdict[entry])[1])
	else:
		for entry in libdict.keys():
			if (libdict[entry])[2]==True:
				pths[entry]=((libdict[entry])[0])	
				TDs[entry]=((libdict[entry])[1])
	# print(pths);print(TDs);
	if not os.path.exists(cachefolder):
		os.makedirs(cachefolder)				
	for f in os.listdir(cachefolder):
		fp = os.path.join(cachefolder, f)
		try:
			shutil.rmtree(fp)
		except OSError:
			os.remove(fp)	
	print("1. Parsing games in device. Please Wait...")			
	process=subprocess.Popen([nscb_mtp,"ShowInstalled","-tfile",games_installed_cache,"-show","false"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	while process.poll()==None:
		if process.poll()!=None:
			process.terminate();	
	if os.path.exists(games_installed_cache):	
		print("   Success")
	gamelist=listmanager.read_lines_to_list(games_installed_cache,all=True)
	installed={}		
	for g in gamelist:
		if exclude_xci==True:
			if g.endswith('xci') or g.endswith('xc0'):
				continue
		entry=listmanager.parsetags(g)
		entry=list(entry)		
		entry.append(g)
		installed[entry[0]]=entry	
	# for i in pths:
		# print(i)
	print("2. Parsing files from Google Drive. Please Wait...")		
	# print(pths)
	if isinstance(pths, dict):
		db={}
		for i in pths.keys():
			db[i]={'path':pths[i],'TD_name':TDs[i]}	
		files=concurrent_scrapper(filter='',order='name_ascending',remotelib='all',db=db)
	else:
		db={}
		db[pths]={'path':pths,'TD_name':TDs}			
		files=concurrent_scrapper(filter=filter,order='name_ascending',remotelib='all',db=db)
	remotelist=[]		
	for f in files:
		remotelist.append(f[0])
	if prioritize_nsz==True:		
		remotelist=sorted(remotelist, key=lambda x: x[-1])	
		remotelist.reverse()	
	else:
		remotelist.reverse()
	# for f in remotelist:
		# print(f)
	remotegames={}		
	for g in remotelist:
		entry=listmanager.parsetags(g)
		entry=list(entry)
		entry.append(g)		
		if not entry[0] in remotegames:
			remotegames[entry[0]]=entry
		else:
			v=(remotegames[entry[0]])[1]
			if int(entry[1])>int(v):
				remotegames[entry[0]]=entry		
	print("3. Searching new updates. Please Wait...")						
	gamestosend={}		
	for g in installed.keys():
		if g.endswith('000') or g.endswith('800'): 
			try:
				updid=g[:-3]+'800'
				if updid in remotegames:
					if updid in installed:
						if ((installed[updid])[1])<((remotegames[updid])[1]):
							if not updid in gamestosend:
								gamestosend[updid]=remotegames[updid]
							else:
								if ((gamestosend[updid])[1])<((remotegames[updid])[1]):
									gamestosend[updid]=remotegames[updid]
					else:
						if not updid in gamestosend:
							gamestosend[updid]=remotegames[updid]
						else:
							if ((gamestosend[updid])[1])<((remotegames[updid])[1]):
								gamestosend[updid]=remotegames[updid]								
			except:pass
		else:
			try:		
				if g in remotegames:
					if ((installed[g])[1])<((remotegames[g])[1]):
						if not g in gamestosend:
							gamestosend[g]=remotegames[g]
						else:
							if ((gamestosend[g])[1])<((remotegames[g])[1]):
								gamestosend[g]=remotegames[g]
			except:pass							
	print("4. Searching new dlcs. Please Wait...")	
	for g in installed.keys():	
		try:
			if g.endswith('000') or g.endswith('800'): 
				baseid=g[:-3]+'000'
			else:
				baseid=(installed[g])[6]
			for k in remotegames.keys():
				try:				
					if not (k.endswith('000') or k.endswith('800')) and not k in installed:
						test=get_dlc_baseid(k)
						if baseid ==test:
							if not k in gamestosend:
								gamestosend[k]=remotegames[k]
							else:
								if ((gamestosend[k])[1])<((remotegames[k])[1]):
									gamestosend[k]=remotegames[k]	
				except BaseException as e:
					# Print.error('Exception: ' + str(e))			
					pass								
		except BaseException as e:
			# Print.error('Exception: ' + str(e))			
			pass
	print("5. List of content that will get installed...")	
	gamepaths=[]
	if len(gamestosend.keys())>0:
		if autoupd_aut==True:	
			for i in sorted(gamestosend.keys()):
				fileid,fileversion,cctag,nG,nU,nD,baseid,path=gamestosend[i]
				bname=os.path.basename(path) 
				gamepaths.append(path)
				g0=[pos for pos, char in enumerate(bname) if char == '[']	
				g0=(bname[0:g0[0]]).strip()
				print(f"   * {g0} [{fileid}][{fileversion}] [{cctag}] - {(bname[-3:]).upper()}")
		else:
			options=[]
			for i in sorted(gamestosend.keys()):			
				fileid,fileversion,cctag,nG,nU,nD,baseid,path=gamestosend[i]
				bname=os.path.basename(path) 
				gamepaths.append(path)
				g0=[pos for pos, char in enumerate(bname) if char == '[']	
				g0=(bname[0:g0[0]]).strip()
				cstring=f"{g0} [{fileid}][{fileversion}] [{cctag}] - {(bname[-3:]).upper()}"
				options.append(cstring)
			if options:
				title = 'Select content to install: \n + Press space or right to select entries \n + Press E to finish selection \n + Press A to select all entries'				
				picker = Picker(options, title, multi_select=True, min_selection_count=1)
				def end_selection(picker):
					return False,-1
				def select_all(picker):
					return "ALL",-1			
				picker.register_custom_handler(ord('e'),  end_selection)
				picker.register_custom_handler(ord('E'),  end_selection)
				picker.register_custom_handler(ord('a'),  select_all)
				picker.register_custom_handler(ord('A'),  select_all)	
				selected=picker.start()					
			if selected[0]==False:
				print("    User didn't select any files")
				return False					
			if selected[0]=="ALL":		
				pass
			else:
				newgpaths=[]
				for game in selected:
					g=game[1]
					g0=gamepaths[g]
					newgpaths.append(g0)
					break
				gamepaths=newgpaths					
		print("6. Generating text file...")		
		with open(tfile,'w', encoding='utf8') as textfile:
			wpath=''
			for i in gamepaths:
				location=None
				for f in files:
					if f[0]==i:	
						location=f[2]
						break
				if location==None:
					print(f"Can't find location for {i}")
					continue
				wpath=f"{location}/{i}"
				textfile.write((wpath).strip()+"\n")	
		print("7. Triggering installer on loop mode.")
		print("   Note:If you interrupt the list use normal install mode to continue list")	
		loop_install(tfile,destiny=destiny,outfolder=None,ch_medium=ch_medium,check_fw=True,patch_keygen=False,ch_base=False,ch_other=False,checked=True)
	else:
		print("\n   --- DEVICE IS UP TO DATE ---")		
	
	
	
	
	