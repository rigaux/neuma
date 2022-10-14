#! /bin/bash

#EXCLUDES='--exclude ".git" --exclude "myenv" --exclude "scorelib/local_settings.py" --exclude "fabfile*'

HOST="neuma.huma-num.fr"
USERNAME="scorelibadmin"
REMOTEPATH="/home/scorelibadmin/scorelib-django"
LOCALPATH="./"
SSHRAPH="/home/raph/.ssh/id_rsa"
SSHPHILIPPE="/Users/philippe/.ssh/id_rsa"
SSHHENRY="/Users/Henry/.ssh/id_rsa"

if [ -f ${SSHRAPH} ]
then
  SSHKEY=${SSHRAPH}
else
  SSHKEY=${SSHPHILIPPE}
fi

SSHCMD="ssh -i ${SSHKEY} -p 22 "

roption=(
    -pthrvz
    --progress
    --exclude='.git'
    --exclude='scorelib/local_settings.py'
    --exclude='fabfile*'
    --exclude='bin'
    --exclude='myvenv/'
    --exclude='__pycache__'
    --exclude='*log'
        --rsh="$SSHCMD"
)

rsync "${roption[@]}" ${LOCALPATH} ${USERNAME}@${HOST}:${REMOTEPATH}
