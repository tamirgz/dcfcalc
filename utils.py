import re

def filtered_to_csv(logger, out_df, out_filename):
    out_df.to_csv("out/" + out_filename, encoding='utf-8', index=False)
    logger.info("[filtered_to_csv] Dataframe saved to file %s" % out_filename)

def raw_to_floats(num): # convert to floats as numbers on MW are represented with a "M" or "B"            
    # multiplier = 1/1000000
    multiplier = 1

    if "M" in num:
        multiplier = 1000000
    if "B" in num:
        multiplier = 1000000000
    if "T" in num:
        multiplier = 1000000000000

    processor = re.compile(r'[^\d.]+')
    try:
        processed_num = float(processor.sub('', num))
        n = processed_num * multiplier
        return n
    except ValueError:
        return 0.0

def raw_to_num(num, multiplier=1): # convert to floats as numbers on MW are represented with a "M" or "B"            
    processor = re.compile(r'[^\d.]+')
    try:
        processed_num = float(processor.sub('', num))
        n = processed_num * multiplier
        return n
    except ValueError:
        return 0.0