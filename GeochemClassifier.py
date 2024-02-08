import sys
import os
import os.path as osp
from shutil import move, rmtree
import pandas as pd


DIRECTORY = r''

REORGANIZE_THIS_DIRECTORY = r''




class GeochemClassifier:

    __VERSION__ = 2.0

    WELCOME = f'''
Geochem Classifier
v{__VERSION__}

Automated geochem data classification assistant.

Developed by: Jakub Pitera 
__________________________________________________

Geochem Classifier will move duplicated filenames aside and perform preliminary classification of geochem files. 
Finally it will produce a report to be used when filling the tracking sheet.

User has to review this classification looking for any outliers and mistakes. PDFs are stored apart for further review.

In order to run this tool prepare the folder structure with appropriate names as following: 
<well> /
    <datapack_1> /
    <datapack_2> / 
    <datapack_3> /
    etc...

Classification is dependant on 'classification_dictionary.csv' which should be curated by the users.
__________________________________________________
'''

    TRANSLATIONS_PATH = r'classification_dictionary.csv'

    def __init__(self):

        self.app_path = os.getcwd()
        self.unique_files = set()
        self.report = pd.DataFrame(
            columns=['FILE AVAILABLE', 'PROCESSED', 'REVIEWED_NOT_PROCESSED',
                     'REASON', 'Datapack', 'WellName', 'File_Name'])

        print(GeochemClassifier.WELCOME)

        try:
            self.translations = self.load_translations(GeochemClassifier.TRANSLATIONS_PATH)
        #    print("Classification dictionary has been loaded successfully.")
        except:
            sys.exit(input("Could not load 'classification_dictionary.csv'. Make sure it is located in the main directory."))

        #input("\nPress enter to run the assistant...\n")

        self.main()

    def main(self):
        """Controls flow of the app. Selects mode"""

        while True:
            mode = self.ask_mode()

            if mode in (1, 2):
                self.run_classifier(mode)
            elif mode == 3:
                self.revert_classifier()
            elif mode == 4:
                self.reorg_dpacks_to_wells()


    @staticmethod
    def ask_mode():
        """Ask user for mode"""

        msg = """
Select  mode:
(1) Single well classification
(2) Bulk well classification
(3) Revert classification
(4) Reorganize from 'by datapack' to 'by well'
"""
        mode = ''
        while mode not in (1, 2, 3, 4):
            try:
                mode = int(input(msg))
            except ValueError:
                continue
        return mode


    def run_classifier(self, mode):
        """Run classifier on all wells depending on mode"""

        # Load wells
        if mode == 1:

            path = input("Insert well directory: ")
            self.directory = osp.dirname(path)
            self.wells = [osp.basename(path)]

            os.chdir(self.directory)

        elif mode == 2:
            path = input("Insert wells directory: ")
            self.directory = path
            os.chdir(self.directory)
            self.wells = [item for item in os.listdir('.') if osp.isdir(item)]

        print("\nClassification is starting...\n")


        for well in self.wells:

            print(f"\n# {well.upper()} WELL #")
            os.chdir(well)

            self.datapacks = [item for item in os.listdir('.') if osp.isdir(item)]

            self.move_duplicates(well)
            print("Duplicates moved.")
            self.classify(well)
            print("Classification completed.")

            os.chdir(self.directory)

        print("\n\nAll files have been classified.")

        self.save_report()

        input("\n")

    @staticmethod
    def load_translations(filepath):
        """Import classification_dictionary.csv """

        d = {}

        with open(filepath, "r") as f:

            next(f)

            for line in f:
                (key, cat, order) = line.strip().split(",")
                order = int(order)

                if order in d.keys():
                    d[order].update({key: cat})
                else:
                    d.update({order: {key: cat}})

        return d

    def __get_files(self):
        pass

    def move_duplicates(self, well_name):
        """Performs check for duplicates on a well"""

        unique = set()
        owd = os.getcwd()
        report_df = self.report.copy()

        for datapack in self.datapacks:

            os.chdir(datapack)

            if not osp.isdir('DUPLICATES'):
                os.mkdir('DUPLICATES')

            for entry in os.scandir():

                if not entry.is_file():
                    continue

                file = entry.name

                if file.upper() in unique:

                    os.rename(file, osp.join('DUPLICATES', file))
                    report_df = report_df.append({'REVIEWED_NOT_PROCESSED': 1,
                                                  'REASON': 'Duplicate',
                                                  'Datapack': datapack,
                                                  'WellName': well_name,
                                                  'File_Name': file},
                                                 ignore_index=True)

                else:
                    unique.add(file.upper())

            os.chdir(owd)

        self.report = report_df.copy()
        self.unique_files = unique.copy()

    def classify(self, well_name):
        """Performs classification on a well"""

        owd = os.getcwd()
        report_df = self.report.copy()

        for datapack in self.datapacks:

            os.chdir(datapack)

            files = [file for file in os.listdir() if osp.isfile(file)]

            for file in files:

                key_found = False

                for ord, keys in sorted(self.translations.items()):

                    if ord == 0:
                        flag = 'PROCESSED'
                    else:
                        flag = 'REVIEWED_NOT_PROCESSED'

                    for key, cat in keys.items():

                        if key in file.upper():

                            key_found = True

                            if cat == 'PDF':
                                key_found = False
                                break

                            if not osp.isdir(flag):
                                os.mkdir(flag)

                            cat_path = osp.join(flag, cat.upper())

                            if not osp.isdir(cat_path):
                                os.mkdir(cat_path)

                            os.rename(file, osp.join(cat_path, file))

                            if flag == 'PROCESSED':
                                report_df = report_df.append({'PROCESSED': 1,
                                                              'Datapack': datapack,
                                                              'WellName': well_name,
                                                              'File_Name': file},
                                                             ignore_index=True)

                            elif flag == 'REVIEWED_NOT_PROCESSED':
                                report_df = report_df.append({'REVIEWED_NOT_PROCESSED': 1,
                                                              'REASON': cat,
                                                              'Datapack': datapack,
                                                              'WellName': well_name,
                                                              'File_Name': file},
                                                             ignore_index=True)
                            break
                    else:
                        continue
                    break

                if not key_found:
                    report_df = report_df.append({'FILE AVAILABLE': 1,
                                                  'Datapack': datapack,
                                                  'WellName': well_name,
                                                  'File_Name': file},
                                                ignore_index=True)

            os.chdir(owd)

        self.report = report_df.copy()

    def save_report(self):
        """Exports report to .csv"""
        self.report \
            .sort_values(['WellName', 'Datapack', 'File_Name'])\
            .to_csv(f"TrackingSheet_report.csv", index=False)

        print("\nReport has been saved!\n")

    def reorg_dpacks_to_wells(self):
        """Reorganizes directory of datapacks/wells into directory of wells/datapacks"""

        wrn = input("""
WARNING!
Entire directory tree will be reorganized in-place. It is not easily reverted. 
Only proceed when sure and possibly data backed up.

Proceed? (yes / no)
""")
        if not wrn.lower()=='yes':
            exit(input('\nSafely exiting'))

        self.directory = input("Insert datapacks directory: ")

        os.chdir(self.directory)

        datapacks = [item for item in os.listdir('.') if osp.isdir(item)]

        for datapack in datapacks:
            wells = [item for item in os.listdir(datapack) if osp.isdir(osp.join(datapack, item))]

            for well in wells:
                move(osp.join(datapack, well), osp.join(well, datapack))

            os.rmdir(datapack)

        print("\n Directory has been reorganized.")

    def revert_classifier(self):
        """Returns all files to original location and clears"""

        self.directory = input("Insert classified wells directory: ")

        os.chdir(self.directory)

        wells = [item for item in os.listdir('.') if osp.isdir(item)]

        for well in wells:
            datapacks = [item for item in os.listdir(well) if osp.isdir(osp.join(well, item))]

            for datapack in datapacks:
                for root, dirs, files in os.walk(osp.join(well, datapack)):
                    for file in files:
                        move(osp.join(root, file), osp.join(well, datapack, file))

                for root, dirs, _ in os.walk(osp.join(well, datapack)):
                    for d in dirs:
                        rmtree(osp.join(root, d))

        input("\n Classification has been reverted.\n")

if __name__ == "__main__":
    gc = GeochemClassifier()
