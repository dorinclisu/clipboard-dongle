import socketpool


class DNSCaptiveServer:
    """Minimal DNS server that responds to all queries with a fixed IP address."""

    def __init__(self, pool, ip_address):
        """
        Initialize the DNS server.

        Args:
            pool: SocketPool instance
            ip_address: IP address to return for all queries
        """
        self.pool = pool or socketpool.SocketPool
        self.ip_address = ip_address
        self.socket = None
        self._running = False
        self._buffer = bytearray(512)  # DNS message buffer

        # Convert IP string to bytes (e.g., "192.168.4.1" -> b'\xc0\xa8\x04\x01')
        self.ip_bytes = bytes(map(int, self.ip_address.split('.')))

    def set_captive_address(self, ip):
        """Set the IP address to return for all DNS queries."""
        self.ip_address = ip
        self.ip_bytes = bytes(map(int, ip.split('.')))

    def start(self, port=53):
        """Start the DNS server on the specified port."""
        if self.socket:
            return

        self.socket = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', port))
        self.socket.settimeout(0.1)  # Non-blocking with timeout
        self._running = True
        print(f"DNS server started on port {port}, responding with {self.ip_address}")

    def stop(self):
        """Stop the DNS server."""
        self._running = False
        if self.socket:
            self.socket.close()
            self.socket = None
            print("DNS server stopped")

    def process_request(self):
        """
        Process a single DNS request if available.
        Returns True if a request was processed, False otherwise.
        """
        if not self.socket:
            return False

        try:
            size, addr = self.socket.recvfrom_into(self._buffer)
            if size < 12:  # Minimum DNS header size
                return False

            data = self._buffer[:size]

            # Extract transaction ID and flags
            txn_id = data[0:2]

            response = bytearray(
                txn_id +                    # Transaction ID (same as query)
                b'\x81\x80' +               # Flags: response, recursion available
                data[4:6] +                 # Question count (from query)
                b'\x00\x01' +               # Answer count = 1
                b'\x00\x00\x00\x00' +       # Authority RR = 0, Additional RR = 0
                data[12:]                   # Original question section
            )

            # Add answer section
            response.extend(
                b'\xc0\x0c' +               # Name pointer (points to name in question at byte 12)
                b'\x00\x01' +               # Type: A record
                b'\x00\x01' +               # Class: IN (Internet)
                b'\x00\x00\x00\x3c' +       # TTL: 60 seconds
                b'\x00\x04'                 # Data length: 4 bytes
            )
            response.extend(self.ip_bytes)  # IP address

            self.socket.sendto(bytes(response), addr)
            return True

        except OSError:  # Timeout or other socket error
            return False

    def serve_forever(self):
        """Run the DNS server in a blocking loop."""
        while self._running:
            self.process_request()
