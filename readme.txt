This is the way I ran it, from a Linux command line:

  python3 comp_pp.py life.txt life.html >test_pp.html

  python3 comp_rt.py life.txt life.html >test_rt.html


The only parts that matter in the files are the 1st 2 paragraphs.
The 1st marks bold with '=' in the text file and '<b></b>' in the html.
The 2nd marks italics with '_' in the text file and several variations in the html.

Your original code shows no differences for the italics, and this for the bold:

    33 : 352       The  = present volume =  lays no claim to literary merit. Two young men,
    34 : 353       led to engage in the whale-fisheries, and spending five years in the
    35 : 354       employment, have compiled from their log-books and their recollection

With my code the above difference no longer occurs.
