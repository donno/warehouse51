#!/usr/bin/awk -f
# AWK Script to process the users file
#
# Test with either:
# $ awk -f process-users.awk users > /rootfs/new-users
# $ ./process-users.awk users
#
# Format:
# [username] [public SSH key]
#
# Other format considered was multiple lines
# USER|
# <name>
# <GECOS>
# <SSH public key>
# USER
# ...
{
    st = index($0," ")
    substr($0,st+1)
    sshkey = substr($0,st+1, length($0)-st-1)
    print "adduser -D " $1;
    print "mkdir -p /home/" $1 "/.ssh && echo \"" sshkey "\" >> /home/" $1 "/.ssh/authorized_keys"
    print "chown -R " $1 ":" $1" /home/" $1 "/.ssh"
    print "chmod 700 /home/" $1 "/.ssh"
    print "chmod 600 /home/" $1 "/.ssh/authorized_keys"

    # Generate fake password.
    #
    # The alternative to this may be to set sshd_config to UsePAM yes and
    # install openssh-server-pam, which allows the accounts to be locked due
    # to having no password but allow ssh access with the keys.
    t1 = rand() * systime(); t2 = rand() * systime()
    fakepwd = sprintf("%x%x", t1, t2)
    print "echo -e \"" fakepwd "\\n" fakepwd "\" | passwd " $1
}
