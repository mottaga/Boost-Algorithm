from random import choice as random_choice
from colorama import Fore, Style, init as colorama_init


# Get the list of used marks from a file
# Params: filepath (string)
# Return: success (boolean), marks (list of strings)
#         failure (boolean), None (None obj)
def load_marks(filepath):
    marks = []
    try:
        f = open(filepath, 'r')
        for line in f:
            if line != '\n':
                marks.append(line.replace('\n', ''))
        f.close()
        return {'status' : True, 'result' : marks}
    except Exception as error:
        #print('Load marks function: ' + str(error)) # Only for debugging
        return {'status' : False, 'error' : str(error)}

# Save the new marks generated into a file
# Params: filepath (string), new_mark (string)
# Return: success / failure (boolean)
def save_mark(filepath, new_mark):
    try:
        f = open(filepath, 'a')
        f.write(new_mark + '\n')
        f.close()
        return {'status' : True}
    except Exception as error:
        #print('Save marks function: ' + str(error)) # Only for debugging
        return {'status' : False, 'error' : str(error)}

# Calculate the accuracy between two marks
# Paramas: mark_one (string), mark_two (string)
# Returns: success (boolean), acc (integer)
#          failure (boolean), None (None obj)
def accuracy(mark_one, mark_two):
    try:
        if (len(mark_one) != len(mark_two)):
            #print('Accuracy function: No matching length') # Only for debugging
            error = 'Accuracy function: No matching length'
            return {'status' : False, 'error' : error}
        acc = 0
        for i in range(len(mark_one)):
            if mark_one[i] == mark_two[i]:
                acc += 1
        acc = ((acc / len(mark_one)) * 100)
        return {'status' : True, 'result' : round(acc, 2)}
    except Exception as error:
        #print('Accuracy function: ' + str(error)) # Only for debugging
        return {'status' : False, 'error' : str(error)}

# Generate a mark for a new device
# Params: marks (list of strings), bits (integer)
# Return: success (boolean), new_mark (string)
#         failure (boolean), None (None obj)
def generate_mark(marks, bits):
    try:
        while True:
            # Generate a random mark
            new_mark = ''
            for i in range(bits):
                new_mark += random_choice(['0', '1'])
            # Check if the mark is acceptable
            max_accuracy = 55
            save = True
            for i in range(len(marks)):
                result = accuracy(marks[i], new_mark)
                if not result['status']:
                    #print('Generate mark function: Accuracy fails') # Only for debugging
                    error = 'Generate mark function: Accuracy fails'
                    return {'status' : False, 'error' : error}
                if result['result'] > max_accuracy:
                    save = False
                    break
            if save:
                return {'status' : True, 'result' : new_mark}
    except Exception as error:
        #print('Generate mark function: ' + str(error)) # Only for debugging
        return {'status' : False, 'error' : str(error)}

# Main
if __name__ == '__main__':
    # Initialize colorama
    colorama_init()
    # Choose the length of the mark
    bits = 1050
    # Load the marks from the file
    result = load_marks('../marks/marks.txt')
    if result['status']:
        marks = result['result']
        # Generate the new mark
        result = generate_mark(marks, bits)
        if result['status']:
            new_mark = result['result']
            # Save the new mark generated
            result = save_mark('../marks/test.txt', new_mark)
            if result['status']:
                print(Fore.GREEN + Style.BRIGHT + '[+]' + Style.RESET_ALL + ' Success: new mark saved')
            else:
                print(Fore.RED + Style.BRIGHT + '[-]' + Style.RESET_ALL + ' Error: could not save the new mark')
        else:
            print(Fore.RED + Style.BRIGHT + '[-]' + Style.RESET_ALL + ' Error: could not generate the new mark')
    else:
        print(Fore.RED + Style.BRIGHT + '[-]' + Style.RESET_ALL + ' Error: could not load the marks')