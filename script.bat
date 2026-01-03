@echo off
:MAIN_MENU
cls
echo ===============================
echo       All-in-One Menu
echo ===============================
echo 1. Docker Compose Menu
echo 2. MongoDB Menu (Docker)
echo 3. Exit
echo ===============================
set /p choice=Choose an option (1-3): 

if "%choice%"=="1" goto DOCKER_MENU
if "%choice%"=="2" goto MONGO_MENU
if "%choice%"=="3" goto END

goto MAIN_MENU

REM ===========================
REM Docker Compose Menu
REM ===========================
:DOCKER_MENU
cls
echo ===============================
echo      Docker Compose Menu
echo ===============================
echo 1. Build images
echo 2. Start container (up)
echo 3. Stop container
echo 4. Down container (no volume)
echo 5. Down container (REMOVE volumes)
echo 6. Restart All Containers (Down -- Build -- Up)
echo 7. Back to Main Menu
echo ===============================
set /p dchoice=Choose an option (1-7): 

if "%dchoice%"=="1" goto BUILD
if "%dchoice%"=="2" goto UP
if "%dchoice%"=="3" goto STOP
if "%dchoice%"=="4" goto DOWN
if "%dchoice%"=="5" goto DOWN_REMOVE_VOLUME
if "%dchoice%"=="6" goto RESTART_ALL
if "%dchoice%"=="7" goto MAIN_MENU

goto DOCKER_MENU

:RESTART_ALL
echo ===============================
echo Restarting All Containers...
echo Down -- Build -- Up
echo ===============================
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml up -d
echo ===============================
echo All containers restarted.
echo ===============================
pause
goto DOCKER_MENU

:BUILD
echo ===============================
echo Building Docker images...
echo ===============================
docker-compose -f docker-compose.yml build
pause
goto DOCKER_MENU

:UP
echo ===============================
echo Starting container...
echo ===============================
docker-compose -f docker-compose.yml up -d
pause
goto DOCKER_MENU

:STOP
echo ===============================
echo Stopping container...
echo ===============================
docker-compose -f docker-compose.yml stop
pause
goto DOCKER_MENU

:DOWN
echo ===============================
echo Bringing down container (NO VOLUME REMOVE)...
echo ===============================
docker-compose -f docker-compose.yml down
pause
goto DOCKER_MENU

:DOWN_REMOVE_VOLUME
echo ===============================
echo Bringing down container (REMOVE VOLUMES)...
echo WARNING: This will delete ALL volumes defined in docker-compose.yml!
echo ===============================
pause
docker-compose -f docker-compose.yml down -v
pause
goto DOCKER_MENU

REM ===========================
REM MongoDB Menu
REM ===========================
:MONGO_MENU
cls
echo ===============================
echo      MongoDB Menu (Docker)
echo ===============================
echo 1. Show all collections
echo 2. Show all data in a collection
echo 3. Show specific data by field and value
echo 4. Back to Main Menu
echo ===============================
set /p mchoice=Choose an option (1-4): 
echo You chose: %mchoice%

if "%mchoice%"=="1" goto SHOW_COLLECTIONS
if "%mchoice%"=="2" goto SHOW_DATA_OF_A_COLLECTION
if "%mchoice%"=="3" goto SHOW_DATA_BY_FIELD
if "%mchoice%"=="4" goto MAIN_MENU

goto MONGO_MENU

:SHOW_COLLECTIONS
cls
echo ===============================
echo Collections in tutor_db
echo ===============================
docker exec -it db mongosh tutor_db --quiet --eval "printjson(db.getCollectionNames());"
pause
goto MONGO_MENU

:SHOW_DATA_OF_A_COLLECTION
cls
set /p collname=Enter collection name: 
echo ===============================
echo Data in collection: %collname%
echo ===============================
docker exec -it db mongosh tutor_db --quiet --eval "db['%collname%'].find().forEach(printjson);"
pause
goto MONGO_MENU

:SHOW_DATA_BY_FIELD
cls
set /p collname=Enter collection name: 
set /p field=Enter field name to filter: 
set /p value=Enter value to match: 
echo ===============================
echo Data in %collname% where %field% = %value%
echo ===============================
docker exec -it db mongosh tutor_db --quiet --eval "db['%collname%'].find({ '%field%': '%value%' }).forEach(printjson);"
pause
goto MONGO_MENU

:END
echo Exiting...
exit
