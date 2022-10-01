# A specialized web-crawler, used to backup the IFMA site

## Installation

   - The project uses Python3

## Running the backup

   - Have a look at the file `config.yaml`, which contains the path to collects and where to store the backup
   - execute `fetchSite`
     The progress is documented in the log file `log.txt`
   - To continuously see the status: run `showAnalysisInLoop`


## Utilities

   ### analyzeUrlsYaml

       Shows the progress and status of the backup process

   ### clean

       Clears the on-going backup files, as preparation to a fresh start

   ### zip_site

       Create a .zip archive of the site

   ### clean_cache_of_redirects

       ???

   ### del_cache_empty_files

       ???

   ### find_in_log

       ???

   ### findStringInCache

       ???

   ### ./test_ana_file.py

       ???

## Author

**Shalom Mitz** - [shalommmitz](https://github.com/shalommmitz)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE ) file for details.

