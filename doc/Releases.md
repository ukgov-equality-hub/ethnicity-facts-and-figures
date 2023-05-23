# Releases

Login to [AWS Console (acc. 049823448487)](https://049823448487.signin.aws.amazon.com/console)

Go to [EC2 Instances](https://eu-west-2.console.aws.amazon.com/ec2/home?region=eu-west-2#Instances:instanceState=running)

Choose the EC2 Instance you want to deploy to and click "Connect".

Choose "EC2 Instance Connect" anc click "Connect"

Run these commands:
* `sudo -i -u eff`  
  to run as the `eff` user
* `cd /home/eff/ethnicity-facts-and-figures-publisher/`  
  to change to the correct directory
* `git fetch`  
  to get the latest code from GitHub
* `git checkout [commit hash]`  
  where `[commit hash]` is the commit hash of the commit you want to checkout  
  e.g. `git checkout cb2f853f6d37633269b327945057bfa29f8caadb`  
  This will warn you about being in a "DETACHED HEAD" state - this is fine
* `exit`  
  to return to the shell as the default `ubuntu` user
* `sudo -i`  
  to run as the root user
* `systemctl restart gunicorn.service`  
  to restart the web server