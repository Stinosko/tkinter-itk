from setuptools import setup, find_packages

VERSION = '0.0.1' 
DESCRIPTION = 'TKinter ITK viewer with plugins and segmentation tools'
LONG_DESCRIPTION = 'TKinter ITK viewer with plugins and segmentation toolsn'

# Setting up
setup(
       # the name must match the folder name 
        name="tkinter_itk",
        version=VERSION,
        author="Stinosko",
        author_email="tkinter_itk.contact@stinosko.com>",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=[], # add any additional packages that 
        # needs to be installed along with your package. Eg: 'caer'
        
        keywords=['python'],
        classifiers= [
            "Development Status :: 2 - Pre-Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 3",
            "Operating System :: Microsoft :: Windows",
        ]
)