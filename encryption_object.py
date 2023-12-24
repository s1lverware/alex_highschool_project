from cryptography.fernet import Fernet

class enc_dec():
    def __init__(self):
        """ The function makes an instance of the class"""
        self.key = None
        self.fernet_object = None
        self.key_path = "/home/pi/Desktop/yb_project_smart_mirror/key.key"
        self.check_if_new_key_needed()
        self.make_fernet_object()
        

    def generate_key(self):
        """ The function generates an encryption key for the fernet object. """
        self.key = Fernet.generate_key()

    def save_key(self):
        """ The function saves the generated key to a file called key.key the the location /home/pi/Desktop/yb_project_smart_mirror/key.key """
        with open(self.key_path, 'wb') as f:
            f.write(self.key)

    def get_key(self):
        """ The function gets the encryption key and saves it to self.key from the file key.key located at /home/pi/Desktop/yb_project_smart_mirror/key.key """
        with open(self.key_path, 'rb') as f:
            key = f.read()
            self.key = key
    
    def check_if_new_key_needed(self):
        """ The function searches for the encryption key and if it doesn't find it, it generates one. """
        try:
            self.get_key()
        except:
            self.generate_key()
            self.save_key()

    def encrypt_message(self, text):
        """ The function gets a string of text that needs to be encrypted. It encrpyts it, encodes it and returns the result. """
        return self.fernet_object.encrypt(text.encode())

    def decrypt_message(self, text):
        """ The function gets an encoded and encrypted string, decrypts it and then decodes it. Later, it returns the result. """
        return self.fernet_object.decrypt(text).decode()

    def make_fernet_object(self):
        """ The finction makes the fernet object that allows the text to be encrypted and decrypted. """
        self.fernet_object = Fernet(self.key)
