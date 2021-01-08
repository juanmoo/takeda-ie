import os
import glob
import codecs
import argparse

def main(input_folder, output_path):

    total = 0
    lines = []
    path_list = sorted(glob.glob(os.path.join(input_folder, '*')))
    #file_list = sorted([os.path.basename(x) for x in path_list])
 
    for i, path in enumerate(path_list):
        with codecs.open(path, 'r', 'utf-8') as fr:
            file_lines = fr.readlines()
            if i == 0:
                lines = lines + file_lines
                total = total + len(file_lines) 
            else:
                lines = lines + ['\n'] + file_lines
                total = total + len(file_lines) + 1
        print('# lines file', i, '= ', len(file_lines))
    
    print('# total lines =', len(lines))
    print(total)
    
    with codecs.open(output_path, 'w', 'utf-8') as fw:
        for line in lines:
            fw.write(line)
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_folder', help = "Input folder with BMES files")
    parser.add_argument('output_path', help = "Path to output merged BMES file")

    args = parser.parse_args()
    input_folder = args.input_folder
    output_path = args.output_path
   
    main(input_folder, output_path)
