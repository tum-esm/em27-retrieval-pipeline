import os
import re
import json
import time
import asyncio
import tarfile
import traceback
from io import BytesIO
from pathlib import Path
from ftplib import FTP, error_perm
from datetime import datetime, timedelta, date

from tqdm import tqdm
from filelock import FileLock
from tenacity import retry, TryAgain, retry_if_exception_type, wait_fixed, stop_after_attempt

from src import utils, types
from src import QueryList

PROJECT_PATH = Path(os.path.abspath(__file__)).parent

#FIXME - any(res := i for i in [1,2,3]) crashes black

def run() -> None:

    execution_start = datetime.utcnow()
    
    try:
    
        # Load and parse the configuration
        config_path = os.path.join(PROJECT_PATH, "config", "config.json")
        with FileLock(config_path + ".lock", timeout=10), open(config_path, "r") as f:
            config = json.load(f, object_hook=lambda c: types.Configuration(**c))

        # Request locations and sensors
        urls = [
            os.path.join(config.location_data, task)
            for task in ("locations.json", "sensors.json")
        ]
        locations_response, sensors_response = asyncio.run(
            utils.get_git_urls(urls, config.git_username, config.git_token)
        )

        # Parse locations
        locations: dict[str, types.Location] = {
            location_tag: types.Location(**data)
            for location_tag, data in locations_response.json().items()
        }

        # Parse sensors and build query lists
        query_lists: dict[tuple[float, float], QueryList] = {}
        for sensor, data in sensors_response.json().items():
            for interval in data["locations"]:

                from_date = datetime.strptime(interval["from_date"], "%Y%m%d").date()
                to_date = datetime.strptime(interval["to_date"], "%Y%m%d").date()

                # Remove sensor locations outside of the requested range
                start = max(from_date, config.from_date)
                end = min(to_date, config.to_date)
                if start <= end:

                    lat = round(locations[interval["location"]].lat)
                    lon = round(locations[interval["location"]].lon)

                    if (lat, lon) not in query_lists:
                        query_lists[(lat, lon)] = QueryList(lat, lon)
                    query_lists[(lat, lon)].insert(start, end, sensor)


        total_nodes = 0
        # Filter, split and combine query lists
        for query_list in query_lists.values():
            query_list.filter(config.dst_directory)
            query_list.split_and_combine()
            total_nodes += len(query_list)

        progress_bar_2014 = tqdm(total=total_nodes)
        progress_bar_2020 = tqdm(total=total_nodes)

        with FTP(
            host="ccycle.gps.caltech.edu",
            user="anonymous",
            passwd=config.email,
            timeout=60,
        ) as ftp:
            
            #ftp.set_debuglevel(1)

            @retry(
                retry=retry_if_exception_type(TryAgain),
                stop=(stop_after_attempt(3)),
                wait=wait_fixed(180)
            )
            async def request_2014() -> None:
                """Requests GGG2014 data."""
                for query_list in query_lists.values():
                    for query in query_list:
                        progress_bar_2014.set_description(
                            f"Curr. Query: {query} {query_list.loc_str()}"
                        )
                        # Build request
                        with BytesIO(
                            "\n".join(
                                (
                                    "tu",
                                    datetime.strftime(query.start, "%Y%m%d"),
                                    datetime.strftime(query.end, "%Y%m%d"),
                                    str(query_list.lat),
                                    str(query_list.lon),
                                    config.email,
                                )
                            ).encode("utf-8")
                        ) as file_:
                            file_.seek(0)
                            
                            try:
                                # Upload request
                                ftp.storbinary("STOR upload/input_file.txt", file_)
                            except error_perm as e:
                                if str(e).split(None, 1)[0] == "553":
                                    # Catch and retry '553 Could not create file.'
                                    raise TryAgain
                                else:
                                    raise e
                                

                        query.status["GGG2014"] = {"request": str(datetime.utcnow())}
                        # Cronjob runs every minute(?)
                        await asyncio.sleep(60)

            @retry(
                retry=retry_if_exception_type(TryAgain),
                stop=(stop_after_attempt(3)),
                wait=wait_fixed(180)
            )
            async def request_2020() -> None:
                """Requests GGG2020 data."""
                for query_list in query_lists.values():
                    for query in query_list:
                        progress_bar_2020.set_description(
                            f"Curr. Query: {query} {query_list.loc_str()}"
                        )
                        # Build request
                        with BytesIO(
                            "\n".join(
                                (
                                    "tu",
                                    datetime.strftime(query.start, "%Y%m%d"),
                                    # Note: GGG2020 end date exclusive
                                    datetime.strftime(query.end + timedelta(1), "%Y%m%d"),
                                    str(query_list.lat),
                                    str(query_list.lon),
                                    config.email,
                                )
                            ).encode("utf-8")
                        ) as file_:
                            file_.seek(0)
                            
                            try:
                                # Upload request
                                ftp.storbinary("STOR upload/input_file_2020.txt", file_)
                            except error_perm as e:
                                if str(e).split(None, 1)[0] == "553":
                                    # Catch and retry '553 Could not create file.'
                                    raise TryAgain
                                else:
                                    raise e

                        query.status["GGG2020"] = {"request": str(datetime.utcnow())}
                        # Cronjob runs every two minutes(?)
                        await asyncio.sleep(120)

            async def await_2014() -> None:
                """Awaits and downloads GGG2014 data."""
                dst_path = f"{config.dst_directory}/GGG2014"

                for query_list in query_lists.values():

                    loc_str = query_list.loc_str()
                    loc_str_com = query_list.loc_str(separate=False)

                    for query in query_list:
                        
                        end = query.end
                        dates = [f"{datetime.strftime(query.start, '%Y%m%d')}_{datetime.strftime(end, '%Y%m%d')}"]

                        # Search for potentially truncated files if the query requests recent dates
                        max_delay = max(query.start, (datetime.utcnow() - timedelta(days=config.max_delay)).date())
                        while (end > max_delay):
                            end -= timedelta(1)
                            dates.append(f"{datetime.strftime(query.start, '%Y%m%d')}_{datetime.strftime(end, '%Y%m%d')}")
                        
                        # GGG2014 data is within different subdirectories
                        map_files = [f"maps/maps_{loc_str_com}_{date}.tar" for date in dates]
                        mod_files = [f"mods/mods_{loc_str_com}_{date}.tar" for date in dates]

                        await_start = time.time()
                        map_, mod_ = False, False
                        while time.time() - await_start < config.max_await_2014:
                            
                            # fmt: off
                            ftp.cwd("upload/modfiles/tar")                     

                            nlst_maps = ftp.nlst("maps")
                            # Search for first matching file with decreasing end date
                            if not map_ and any(map_file := f for f in map_files if f in nlst_maps):
                                with BytesIO() as file_:
                                    ftp.retrbinary(
                                        f"RETR {map_file}",
                                        file_.write,
                                    )
                                    file_.seek(0)
                                    # Extract, rename and store members
                                    with tarfile.open(fileobj=file_) as tar:
                                        for member in tar:
                                            member.name = f"{member.name[2:10]}_{loc_str}.map"
                                            for sensor in query.sensors:
                                                tar.extract(member, f"{dst_path}/map/{sensor}")

                                map_ = True

                            nlst_mods = ftp.nlst("mods")
                            # Search for first matching file with decreasing end date
                            if not mod_ and any(mod_file := f for f in mod_files if f in nlst_mods):
                                with BytesIO() as file_:
                                    ftp.retrbinary(
                                        f"RETR {mod_file}",
                                        file_.write,
                                    )
                                    file_.seek(0)
                                    # Extract, rename and store members
                                    with tarfile.open(fileobj=file_) as tar:
                                        for member in tar:
                                            member.name = f"{member.name[5:13]}_{loc_str}.mod"
                                            for sensor in query.sensors:
                                                tar.extract(member, f"{dst_path}/mod/{sensor}")
                                mod_ = True
                                
                            if map_ and mod_:
                                query.status["GGG2014"]["download"] = str(datetime.utcnow())
                                query.status["GGG2014"]["files"] = [map_file, mod_file]
                                progress_bar_2014.update(1)
                                ftp.cwd("/")
                                break

                            ftp.cwd("/")
                            await asyncio.sleep(30)
                            # fmt: on
                        
                        else:
                            #FIXME - Adjust for async. version
                            query.status["GGG2014"]["download"] = "Timeout"
                            return 


            async def await_2020() -> None:
                """Awaits and downloads GGG2020 data."""
                dst_path = f"{config.dst_directory}/GGG2020"

                for query_list in query_lists.values():

                    loc_str = query_list.loc_str()
                    loc_str_dec = query_list.loc_str(decimals=True)

                    for query in query_list:

                        end = query.end + timedelta(1)
                        dates = [f"{datetime.strftime(query.start, '%Y%m%d')}-{datetime.strftime(end, '%Y%m%d')}"]
                        
                        # Search for potentially truncated files if the query requests recent dates
                        max_delay = max(query.start + timedelta(1),
                                        (datetime.utcnow() - timedelta(days=config.max_delay-1)).date())
                        while (end > max_delay):
                            end -= timedelta(1)
                            dates.append(f"{datetime.strftime(query.start, '%Y%m%d')}-{datetime.strftime(end, '%Y%m%d')}")
                        
                        # GGG2020 data is within one .tgz file
                        suffixes = [f"{loc_str_dec}_{date}.tgz" for date in dates]

                        await_start = time.time()
                        while (time.time() - await_start < config.max_await_2020):

                            ftp.cwd("ginput-jobs")

                            # fmt: off
                            nlst = ftp.nlst()
                            # Search for first matching file with decreasing end date
                            if any (tgz := t for s in suffixes for t in nlst if t.endswith(s)):
                                
                                with BytesIO() as file_:
                                    ftp.retrbinary(
                                        f"RETR {tgz}",
                                        file_.write,
                                    )
                                    file_.seek(0)
                                    # Extract, rename and store members
                                    with tarfile.open(fileobj=file_) as tar:
                                        for member in tar:
                                            name = member.name

                                            if name.endswith(".map"):
                                                member.name = f"{name[47:55]}_{name[55:57]}_{loc_str}.map"
                                                for sensor in query.sensors:
                                                    tar.extract(
                                                        member,
                                                        f"{dst_path}/map/{sensor}/{name[47:55]}_{loc_str}",
                                                    )

                                            elif name.endswith(".mod"):
                                                member.name = f"{name[35:43]}_{name[43:45]}_{loc_str}.mod"
                                                for sensor in query.sensors:
                                                    tar.extract(
                                                        member,
                                                        f"{dst_path}/mod/{sensor}/{name[35:43]}_{loc_str}",
                                                    )

                                            elif name.endswith(".vmr"):
                                                member.name = f"{name[39:47]}_{name[47:49]}_{loc_str}.vmr"
                                                for sensor in query.sensors:
                                                    tar.extract(
                                                        member,
                                                        f"{dst_path}/vmr/{sensor}/{name[39:47]}_{loc_str}",
                                                    )
                                query.status["GGG2020"]["download"] = str(datetime.utcnow())
                                query.status["GGG2020"]["file"] = tgz
                                progress_bar_2020.update(1)
                                ftp.cwd("/")
                                break
                            
                            ftp.cwd("/")
                            await asyncio.sleep(300)
                            # fmt: on
                        
                        else:
                            #FIXME - Adjust for async. version
                            query.status["GGG2020"]["download"] = "Timeout"
                            return
                            
                            
            async def _tasks() -> None:
                tasks = (
                    asyncio.create_task(request_2014()),
                    asyncio.create_task(request_2020()),
                    asyncio.create_task(await_2014()),
                    asyncio.create_task(await_2020()),
                )
                await asyncio.gather(*tasks)

            asyncio.run(_tasks())

        # Create report summary
        report_name = datetime.utcnow().strftime("report_%Y%m%d_%H%M")
        with open(f"{PROJECT_PATH}/reports/{report_name}.json", "w") as file_:
            json.dump(
                {
                    "executionStart": str(execution_start),
                    "executionTime": str(datetime.utcnow() - execution_start),
                    "totalNodes": total_nodes,
                    "uploadBlocked": {
                        "GGG2014": request_2014.retry.statistics["attempt_number"] -1, #type: ignore
                        "GGG2020": request_2020.retry.statistics["attempt_number"] -1 #type: ignore
                    },
                    "queryLists": [q.to_json() for q in query_lists.values()],
                },
                file_,
                indent=4,
            )
    
    except Exception:
        
        # Report unexpected exceptions
        print(traceback.format_exc())
        report_name = datetime.utcnow().strftime("report_%Y%m%d_%H%M")
        with open(f"{PROJECT_PATH}/reports/{report_name}.json", "w") as file_:
            json.dump(
                {
                    "executionStart": str(execution_start),
                    "executionTime": str(datetime.utcnow() - execution_start),
                    "exception": traceback.format_exc()
                },
                file_,
                indent=4,
            )

if __name__ == "__main__":
    run()
