from src import main

# Config Load: Errors will be thrown anyway
# Validators: Dirs will be created anyway, Errors thrown anyway
# Pydantic Types
# Double request/joins?
# Database interface
# Last ends with null / check if get_loc_data is enough to adjust ends
# Database problem no types as usual
#query = f"""
#        SELECT *
#        FROM measurements m
#        WHERE m.retrieval_software = '{config.campaign}' AND m.sensor IN ({sensors}) AND );
#        
#    """

if __name__ == "__main__":
    main.run()
