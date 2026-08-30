import os
import platform
import shutil
import re
import subprocess
import sys

# init exec locations
# maybe just like run from path cuz uh this is terrible
# dont do as i do, do i as i say.
match platform.system():
	case "Windows":
		arkhelper_path = "./dependencies/arkhelper"
		wit_path       = "./dependencies/wit/wit"
	case "Linux":
		arkhelper_path = "./dependencies/linux/arkhelper"
		wit_path       = "./dependencies/wit/wit"
	case "Darwin":
		arkhelper_path = "./dependencies/macos/arkhelper"
		wit_path       = "./dependencies/wit/wit_macos"

def build_ark(srcs, dest, temp_ark, ark_name, game, excludes, split_size = "2147483647"):
	make_temp_ark(srcs, temp_ark, excludes)

	# build ark
	run = [arkhelper_path, "dir2ark",  temp_ark, dest, "-n", ark_name, "-s", split_size]
	match game:
		case "rb1":
			run.extend(["-e", "-v", "4"])
		case "rb1_patch":
			run.extend(["-e", "-v", "4", "-f"])
		case "rb2" | "lrb" | "tbrb" | "gdrb":
			run.extend(["-e", "-v", "5"])
		case "rb3" | "blitz":
			run.extend(["-e", "-v", "6"])
	subprocess.run(run)

	# delete temp path
	shutil.rmtree(temp_ark)

def build_patchark(srcs, dest, temp_ark, hdr_path, excludes):
	make_temp_ark(srcs, temp_ark, excludes)

	# build ark
	run = [arkhelper_path, "patchcreator",  hdr_path, "./dependencies/null", "-a", temp_ark, "-o", dest]
	subprocess.run(run)

	# remove null "exec"
	os.remove(dest + "/null")

	# delete temp path
	shutil.rmtree(temp_ark)

def build_splitark(srcs, dest, temp_ark, ark_name, game, hdr_path, excludes):
	make_temp_ark(srcs, temp_ark, excludes)

	size = 0
	for path, dirs, files in os.walk(temp_ark):
		for file in files:
			fp = os.path.join(path, file)
			size += os.path.getsize(fp)
	if size > 2147483647:
		print("size above limit! attempting to split")
		temp_ark1 = temp_ark + "1"
		if os.path.exists(temp_ark1):
			shutil.rmtree(temp_ark1)
		os.mkdir(temp_ark1)
		
		while size > 2147483647:
			# maybe this should be optimised :)
			# also looking at this kinda hurts my head
			largest_size = 0
			largest_file = ""
			largest_file_path = ""
			for path, dirs, files in os.walk(temp_ark):
				for file in files:
					fp = os.path.join(path, file)
					file_size = os.path.getsize(fp)
					if file_size > largest_size:
						largest_file = fp
						largest_size = file_size
						largest_file_path = path

			file_temp = largest_file.replace(temp_ark, temp_ark1)
			dirpath_temp = largest_file_path.replace(temp_ark, temp_ark1)

			os.makedirs(dirpath_temp, exist_ok=True)
			shutil.move(largest_file, file_temp)
			size -= largest_size
	# build ark
	run = [arkhelper_path, "dir2ark",  temp_ark, dest, "-n", ark_name, "-s", "2147483647"]
	match game:
		case "rb1":
			run.extend(["-e", "-v", "4"])
		case "rb1_patch":
			run.extend(["-e", "-v", "4", "-f"])
		case "rb2" | "lrb" | "tbrb" | "gdrb":
			run.extend(["-e", "-v", "5"])
		case "rb3" | "blitz":
			run.extend(["-e", "-v", "6"])
	subprocess.run(run)

	# delete temp path
	shutil.rmtree(temp_ark)

	if 'temp_ark1' in locals() and temp_ark1:
		dest = dest.replace("gen/", "")
		dest = dest.replace("gen", "")

		# build ark
		run = [arkhelper_path, "patchcreator",  hdr_path, "./dependencies/null", "-a", temp_ark1, "-o", dest]
		subprocess.run(run)

		# remove null "exec"
		os.remove(dest + "/null")

		# delete temp path
		shutil.rmtree(temp_ark1)

def make_temp_ark(srcs, temp_ark, excludes):
	# delete temp path if it exists
	if os.path.exists(temp_ark):
		shutil.rmtree(temp_ark)

	os.mkdir(temp_ark)

	# create temp ark folder with only relevant files
	for path in srcs:
		if type(path) == list:
			path_as = path[1]
			path = path[0]
		else:
			path_as = False
		for dirpath, dirnames, filenames in os.walk(path):
			for name in filenames:
				file = os.path.join(dirpath, name)
				include = True

				# match file through all regex paterns
				# idk python maybe optize this with like while or something
				for exclude in excludes:
					if re.search(exclude, file):
						include = False

				if include:
					if path_as:
						file_temp = file.replace(path, temp_ark + path_as)
						dirpath_temp = dirpath.replace(path, temp_ark + path_as)
					else:
						file_temp = file.replace(path, temp_ark)
						dirpath_temp = dirpath.replace(path, temp_ark)

					# make dirs and copy/link files
					os.makedirs(dirpath_temp, exist_ok=True)
					if platform.system() == "Windows":
						shutil.copy(file, file_temp)
					else:
						subprocess.run(["ln", file, file_temp, "-f"])

def wii_init(iso_folder, ext_path, to_add):
	if not os.path.exists(ext_path):
		print("extracting wbfs")
		subprocess.run([wit_path, "extract", iso_folder, ext_path])
		if not os.path.exists(ext_path):
			sys.exit("failed to extract wbfs")
	print("copying base wii files")
	for dirpath, dirnames, filenames in os.walk(to_add):
		for name in filenames:
			file = os.path.join(dirpath, name)
			file_temp = file.replace(to_add, ext_path)
			dirpath_temp = dirpath.replace(to_add, ext_path)

			# make dirs and copy files
			os.makedirs(dirpath_temp, exist_ok=True)
			shutil.copy(file, file_temp)

def make_wbfs(ext_path, output_file):
	if os.path.exists(output_file):
		print("removing existing wbfs")
		os.remove(output_file)
	print("making wbfs. THIS WILL TAKE A VERY LONG TIME!!!!!")
	subprocess.run([wit_path, "copy", ext_path, output_file])
	print("wbfs made")

