# Whole-History Rating for Renju
Whole-History Rating for Renju. The Rating is published at https://renjurating.wind23.com/.

It is calculated based on the [WHR algorithm](https://www.remi-coulom.fr/WHR/) by Rémi Coulom, a similar approach as the [Go Ratings](https://www.goratings.org/en/). The core algorithm is based on the [open source code](https://github.com/wind23/whole_history_rating) on Github.

# How to run the script
To run the script, you need to have `Python 3`, with the package `whr` and `yattag` installed. You can simply install them with pip:

    pip install whr
    pip install yattag
    
To compute the rating, at first, you need to download the database here: https://www.renju.net/game/. The downloaded database will have a filename such as `renjunet_v10_20210827.rif`. Put this database into the directory `data`.

After the database is ready, you can simply run:

    python compute_rating.py [yyyymmdd] [CATEGORY]
    
Replace `[yyyymmdd]` with the same date as the database, such as `20210827`. `[CATEGORY]` is either `renju` or `gomoku`. Run the script, and the rating will be generated in the directory `html_renju` or `html_gomoku`.
