import secrets

def gerar_secret_key(tamanho=32):
    """
    Gera uma chave secreta aleatória com o tamanho especificado em bytes.
    O padrão é 32 bytes (256 bits), que é suficientemente seguro para JWT.
    
    Args:
        tamanho (int): Tamanho da chave em bytes. Padrão é 32.
    
    Returns:
        str: Chave secreta em formato hexadecimal.
    """
    # Gera bytes aleatórios usando o módulo secrets
    chave_bytes = secrets.token_bytes(tamanho)
    # Converte os bytes para uma string hexadecimal
    chave_hex = chave_bytes.hex()
    return chave_hex

if __name__ == "__main__":
    # Gera uma chave secreta de 32 bytes (64 caracteres em hexadecimal)
    secret_key = gerar_secret_key()
    print("Sua SECRET_KEY gerada é:")
    print(secret_key)
    print("\nCopie e cole esta chave no seu código Flask em app.config['SECRET_KEY']")
    print("Guarde-a em um local seguro e não a compartilhe publicamente!")