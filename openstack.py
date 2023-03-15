import openstack

SERVER_NAME = 'web-tier-instance'
IMAGE_NAME = 'web-tier-image'
FLAVOR_NAME = 'm1.small'
NETWORK_NAME = 'private'
KEYPAIR_NAME = 'web-tier-key'
PRIVATE_KEYPAIR_FILE = 'id_web'


def create_server(conn):
    print("Create Server:")

    image = conn.compute.find_image(IMAGE_NAME)
    flavor = conn.compute.find_flavor(FLAVOR_NAME)
    network = conn.network.find_network(NETWORK_NAME)
    keypair = conn.compute.find_keypair(KEYPAIR_NAME)

    server = conn.compute.create_server(
        name=SERVER_NAME, image_id=image.id, flavor_id=flavor.id,
        networks=[{"uuid": network.id}], key_name=keypair.name)

    server = conn.compute.wait_for_server(server, wait=360)

    print("ssh -i {key} ubuntu@{ip}".format(
        key=PRIVATE_KEYPAIR_FILE,
        ip=server.access_ipv4))


def delete_server(conn):
    print("Delete Server:")
    server = conn.compute.find_server(SERVER_NAME)
    print(server)
    conn.compute.delete_server(server)


with openstack.connect(cloud='openstack') as conn:
    create_server(conn)
    # delete_server(conn)
