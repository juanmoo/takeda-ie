import glob
import codecs

input_path = 'C:\\Users\\siban\\Dropbox\\CSAIL\\Projects\\02_Github\\takeda_nlp\\00_data\\01_BMES\\*'
output_path = 'C:\\Users\\siban\\Dropbox\\CSAIL\\Projects\\02_Github\\takeda_nlp\\00_data\\01_BMES\\BMES_merged'

total = 0
lines = []
for i, path in enumerate(glob.glob(input_path)):
    with codecs.open(path, 'r', 'utf-8') as fr:
        file_lines = fr.readlines()
        lines = lines + file_lines
        total = total + len(file_lines)
        print('# lines file', i, '= ', len(file_lines))

print('# total lines =', len(lines))
print(total)

with codecs.open(output_path, 'w', 'utf-8') as fw:
    for line in lines:
        fw.write(line)
