"use strict";
//==================================================
// Interface
//==================================================
// ﾌﾞﾗｳｻﾞ上で再生されている音声を自動検索(isPlaying)
// Web Audio APIで16bit PCMﾃﾞｰﾀに変換
// QWebChannelでPythonへBase64で送信(ﾌﾞﾘｯｼﾞ)
// 音声ﾌｧｲﾙの場合は直接取得(fetch), ｽﾄﾘｰﾐﾝｸﾞの場合はﾗｲﾌﾞｷｬﾌﾟﾁｬ(captureStream)
// 音声の最後に2秒無音
// ﾌﾟﾘﾛｰﾙ: 録音開始直前の数秒を保存(常時)
//==================================================
// Main Entry Point & Setup
//==================================================
//MARK:main
(function () {
    if (window.isShigeAudioRec) {
        return;
    }
    //MARK:setupRecorder
    function setupRecorder() {
        const qtExists = typeof qt !== 'undefined';
        const qtTransportExists = qt && qt.webChannelTransport;
        const qwebchannelExists = typeof QWebChannel !== 'undefined';
        if (!qtExists || !qtTransportExists || !qwebchannelExists) {
            return;
        }
        if (window.isShigeAudioRec) {
            return;
        }
        window.isShigeAudioRec = true;
        //==================================================
        // Recorder
        //==================================================
        //MARK:ShigeRecorder
        const recorder = {
            bridge: null,
            mediaStream: null,
            audioContext: null,
            sourceNode: null,
            processorNode: null,
            silentGainNode: null,
            monitoredElement: null,
            strSessionId: null,
            isSessionActive: false,
            isStartPending: false,
            monitorRetryTimerId: null,
            sampleRate: 44100,
            channelCount: 1,
            processorBufferSize: 4096,
            preRollChunkLimit: 6,
            preRollChunks: [],
            //==================================================
            // Bridge & Error Handling
            //==================================================
            checkBridge(callback) {
                if (this.bridge) {
                    if (callback) {
                        callback();
                    }
                    return;
                }
                new QWebChannel(qt.webChannelTransport, (channel) => {
                    this.bridge = channel.objects.shigeAudioRecorder;
                    if (callback) {
                        callback();
                    }
                });
            },
            //MARK:reportError
            reportError(message) {
                if (this.bridge && this.bridge.onRecError) {
                    this.bridge.onRecError(String(message));
                }
            },
            //==================================================
            // Media Element Search
            //==================================================
            //MARK:findActive
            findActive() {
                const allMediaElements = document.querySelectorAll('audio, video');
                let foundActiveElement = null;
                for (let index = 0; index < allMediaElements.length; index++) {
                    const currentElement = allMediaElements[index];
                    const isNotPaused = !currentElement.paused;
                    const isNotEnded = !currentElement.ended;
                    const canPlay = currentElement.readyState > 0;
                    const isPlaying = isNotPaused && isNotEnded && canPlay;
                    if (isPlaying) {
                        foundActiveElement = currentElement;
                        break;
                    }
                }
                return foundActiveElement;
            },
            //MARK:findPrepared
            findPrepared() {
                const allMediaElements = document.querySelectorAll('audio, video');
                let firstUsableElement = null;
                for (let index = 0; index < allMediaElements.length; index++) {
                    const currentElement = allMediaElements[index];
                    if (currentElement.ended) {
                        continue;
                    }
                    if (currentElement.readyState > 0) {
                        return currentElement;
                    }
                    if (!firstUsableElement) {
                        firstUsableElement = currentElement;
                    }
                }
                return firstUsableElement;
            },
            //==================================================
            // Stream and PCM
            //==================================================
            //MARK:getStream
            getStream(element) {
                if (!element) {
                    return null;
                }
                const elementAsAnyType = element;
                if (typeof elementAsAnyType.captureStream === 'function') {
                    return elementAsAnyType.captureStream();
                }
                return null;
            },
            //MARK:createSessionId
            createSessionId() {
                const randomString = Math.random().toString(16).slice(2);
                return `recording_${Date.now()}_${randomString}`;
            },
            //MARK:isDownloadableMimeType
            isDownloadableMimeType(mimeType) {
                const normalizedMimeType = (mimeType || '').toLowerCase();
                if (!normalizedMimeType) {
                    return false;
                }
                const supportedMimeTypes = [
                    'audio/mpeg',
                    'audio/mp3',
                    'audio/ogg',
                    'audio/wav',
                    'audio/x-wav',
                    'audio/x-m4a',
                    'audio/mp4',
                    'audio/aac',
                    'audio/flac',
                    'audio/opus'
                ];
                for (let index = 0; index < supportedMimeTypes.length; index++) {
                    if (normalizedMimeType.indexOf(supportedMimeTypes[index]) === 0) {
                        return true;
                    }
                }
                return false;
            },
            //MARK:isDownloadableUrl
            isDownloadableUrl(url) {
                if (!url) {
                    return false;
                }
                const normalizedUrl = url.trim();
                if (!normalizedUrl ||
                    normalizedUrl.startsWith('blob:') ||
                    normalizedUrl.startsWith('data:') ||
                    normalizedUrl.startsWith('mediastream:')) {
                    return false;
                }
                try {
                    const parsedUrl = new URL(normalizedUrl, window.location.href);
                    const protocol = parsedUrl.protocol.toLowerCase();
                    if (protocol !== 'http:' && protocol !== 'https:') {
                        return false;
                    }
                    const lowerPath = parsedUrl.pathname.toLowerCase();
                    const fileExtensions = [
                        '.mp3',
                        '.ogg',
                        '.oga',
                        '.wav',
                        '.m4a',
                        '.aac',
                        '.flac',
                        '.opus'
                    ];
                    for (let index = 0; index < fileExtensions.length; index++) {
                        if (lowerPath.endsWith(fileExtensions[index])) {
                            return true;
                        }
                    }
                }
                catch (_error) {
                    return false;
                }
                return false;
            },
            //MARK:guessMimeTypeFromUrl
            guessMimeTypeFromUrl(url) {
                const lowerUrl = url.toLowerCase();
                if (lowerUrl.includes('.mp3')) {
                    return 'audio/mpeg';
                }
                if (lowerUrl.includes('.ogg') || lowerUrl.includes('.oga')) {
                    return 'audio/ogg';
                }
                if (lowerUrl.includes('.wav')) {
                    return 'audio/wav';
                }
                if (lowerUrl.includes('.m4a')) {
                    return 'audio/x-m4a';
                }
                if (lowerUrl.includes('.aac')) {
                    return 'audio/aac';
                }
                if (lowerUrl.includes('.flac')) {
                    return 'audio/flac';
                }
                if (lowerUrl.includes('.opus')) {
                    return 'audio/opus';
                }
                return 'application/octet-stream';
            },
            //MARK:findDownloadSource
            findDownloadSource(element) {
                if (!element) {
                    return null;
                }
                const candidates = [];
                const seenUrls = {};
                const addCandidate = (url, mimeType) => {
                    const normalizedUrl = (url || '').trim();
                    if (!normalizedUrl || seenUrls[normalizedUrl]) {
                        return;
                    }
                    seenUrls[normalizedUrl] = true;
                    candidates.push({
                        url: normalizedUrl,
                        mimeType: (mimeType || '').trim()
                    });
                };
                addCandidate(element.currentSrc, element.getAttribute('type'));
                addCandidate(element.src, element.getAttribute('type'));
                const sourceElements = element.querySelectorAll('source');
                for (let index = 0; index < sourceElements.length; index++) {
                    const currentSource = sourceElements[index];
                    addCandidate(currentSource.src, currentSource.type);
                }
                for (let index = 0; index < candidates.length; index++) {
                    const currentCandidate = candidates[index];
                    const hasDirectUrl = this.isDownloadableUrl(currentCandidate.url);
                    const hasDirectMimeType = this.isDownloadableMimeType(currentCandidate.mimeType);
                    if (!hasDirectUrl && !hasDirectMimeType) {
                        continue;
                    }
                    return {
                        url: currentCandidate.url,
                        mimeType: currentCandidate.mimeType || this.guessMimeTypeFromUrl(currentCandidate.url)
                    };
                }
                return null;
            },
            //MARK:requestAudioFileDownload
            requestAudioFileDownload(source) {
                if (!this.bridge || !this.isStartPending) {
                    return false;
                }
                this.clearRetry();
                try {
                    const sessionId = this.createSessionId();
                    const mimeType = source.mimeType || this.guessMimeTypeFromUrl(source.url);
                    this.bridge.downloadAudioUrl(sessionId, source.url, mimeType);
                    this.isStartPending = false;
                    this.isSessionActive = false;
                    this.strSessionId = null;
                    this.clearBuffer();
                    return true;
                }
                catch (error) {
                    this.reportError(`Direct audio url handoff failed: ${error}`);
                    this.isSessionActive = false;
                    this.strSessionId = null;
                    return false;
                }
            },
            //MARK:makePcmType
            makePcmType() {
                return `audio/pcm;rate=${this.sampleRate};channels=${this.channelCount};format=s16le`;
            },
            //MARK:bufToBase64
            bufToBase64(buffer) {
                const bytes = new Uint8Array(buffer);
                const chunkSize = 0x8000;
                let binary = '';
                for (let chunkStart = 0; chunkStart < bytes.length; chunkStart += chunkSize) {
                    const slice = bytes.subarray(chunkStart, chunkStart + chunkSize);
                    let sliceString = '';
                    for (let byteIndex = 0; byteIndex < slice.length; byteIndex++) {
                        const charCode = slice[byteIndex];
                        sliceString += String.fromCharCode(charCode);
                    }
                    binary += sliceString;
                }
                return btoa(binary);
            },
            //MARK:encodeInputToPcm
            encodeInputToPcm(inputBuffer) {
                if (!this.channelCount || inputBuffer.length <= 0) {
                    return null;
                }
                const channelDataList = [];
                for (let channelIndex = 0; channelIndex < this.channelCount; channelIndex++) {
                    channelDataList.push(inputBuffer.getChannelData(channelIndex));
                }
                const pcmBuffer = new ArrayBuffer(inputBuffer.length * this.channelCount * 2);
                const pcmView = new DataView(pcmBuffer);
                let offset = 0;
                for (let sampleIndex = 0; sampleIndex < inputBuffer.length; sampleIndex++) {
                    for (let channelIndex = 0; channelIndex < this.channelCount; channelIndex++) {
                        const sample = channelDataList[channelIndex][sampleIndex] || 0;
                        pcmView.setInt16(offset, this.clampSampleToInt16(sample), true);
                        offset += 2;
                    }
                }
                return this.bufToBase64(pcmBuffer);
            },
            //MARK:clampSampleToInt16
            clampSampleToInt16(sample) {
                const clamped = Math.max(-1, Math.min(1, sample));
                if (clamped < 0) {
                    return Math.round(clamped * 0x8000);
                }
                return Math.round(clamped * 0x7fff);
            },
            //==================================================
            // Buffer
            //==================================================
            //MARK:queueChunk
            queueChunk(chunk) {
                this.preRollChunks.push(chunk);
                while (this.preRollChunks.length > this.preRollChunkLimit) {
                    this.preRollChunks.shift();
                }
            },
            //MARK:clearBuffer
            clearBuffer() {
                this.preRollChunks = [];
            },
            //MARK:flushChunks
            flushChunks() {
                if (!this.bridge || !this.strSessionId || this.preRollChunks.length <= 0) {
                    return;
                }
                const bufferedChunks = this.preRollChunks.slice();
                this.clearBuffer();
                for (let index = 0; index < bufferedChunks.length; index++) {
                    this.bridge.appendRecChunk(this.strSessionId, bufferedChunks[index]);
                }
            },
            //==================================================
            // Monitoring and Session Control
            //==================================================
            //MARK:hasLiveAudio
            hasLiveAudio() {
                if (!this.mediaStream) {
                    return false;
                }
                const audioTracks = this.mediaStream.getAudioTracks();
                if (audioTracks.length <= 0) {
                    return false;
                }
                for (let index = 0; index < audioTracks.length; index++) {
                    if (audioTracks[index].readyState === 'live') {
                        return true;
                    }
                }
                return false;
            },
            //MARK:clearRetry
            clearRetry() {
                if (this.monitorRetryTimerId !== null) {
                    window.clearTimeout(this.monitorRetryTimerId);
                    this.monitorRetryTimerId = null;
                }
            },
            //MARK:scheduleRetry
            scheduleRetry() {
                if (this.monitorRetryTimerId !== null) {
                    return;
                }
                this.monitorRetryTimerId = window.setTimeout(() => {
                    this.monitorRetryTimerId = null;
                    this.monitor();
                }, 250);
            },
            //MARK:beginSession
            beginSession() {
                if (this.isSessionActive || !this.isStartPending || !this.bridge || !this.audioContext) {
                    return;
                }
                this.strSessionId = this.createSessionId();
                this.isSessionActive = true;
                this.isStartPending = false;
                this.bridge.onRecording(this.strSessionId, this.makePcmType());
                this.flushChunks();
            },
            //MARK:monitor
            monitor() {
                if (!this.isStartPending && !this.isSessionActive) {
                    if (this.audioContext || this.processorNode || this.mediaStream) {
                        void this.onCleanup();
                    }
                    return;
                }
                if (this.audioContext && this.processorNode && this.hasLiveAudio()) {
                    this.beginSession();
                    return;
                }
                if (this.audioContext || this.processorNode || this.mediaStream) {
                    void this.onCleanup().then(() => {
                        if (this.isStartPending || this.isSessionActive) {
                            this.monitor();
                        }
                    });
                    return;
                }
                const sourceElement = this.findActive();
                if (!sourceElement) {
                    this.scheduleRetry();
                    return;
                }
                const directSource = this.findDownloadSource(sourceElement);
                if (directSource) {
                    const didQueueDownload = this.requestAudioFileDownload(directSource);
                    if (!didQueueDownload && (this.isStartPending || this.isSessionActive)) {
                        this.monitor();
                    }
                    return;
                }
                const capturedStream = this.getStream(sourceElement);
                const hasStream = capturedStream !== null;
                const hasAudio = !!(capturedStream &&
                    capturedStream.getAudioTracks().length > 0);
                if (!hasStream || !hasAudio) {
                    this.scheduleRetry();
                    return;
                }
                this.initAudio(capturedStream, sourceElement);
            },
            //==================================================
            // Audio Graph and Cleanup
            //==================================================
            //MARK:initAudio
            initAudio(capturedStream, sourceElement) {
                const AudioContextClass = window.AudioContext || null;
                if (!AudioContextClass) {
                    this.reportError('Web Audio API is not available.');
                    return;
                }
                this.clearRetry();
                this.mediaStream = capturedStream;
                this.monitoredElement = sourceElement;
                try {
                    this.audioContext = new AudioContextClass();
                    this.sampleRate = this.audioContext.sampleRate;
                    this.sourceNode = this.audioContext.createMediaStreamSource(capturedStream);
                    const streamChannelCount = Math.max(1, Math.min(2, capturedStream.getAudioTracks().length));
                    this.channelCount = streamChannelCount;
                    this.processorNode = this.audioContext.createScriptProcessor(this.processorBufferSize, this.channelCount, this.channelCount);
                    this.silentGainNode = this.audioContext.createGain();
                    this.silentGainNode.gain.value = 0;
                    this.processorNode.onaudioprocess = (event) => {
                        const base64Chunk = this.encodeInputToPcm(event.inputBuffer);
                        if (!base64Chunk) {
                            return;
                        }
                        this.queueChunk(base64Chunk);
                        if (!this.isSessionActive || !this.bridge || !this.strSessionId) {
                            return;
                        }
                        this.bridge.appendRecChunk(this.strSessionId, base64Chunk);
                    };
                    this.sourceNode.connect(this.processorNode);
                    this.processorNode.connect(this.silentGainNode);
                    this.silentGainNode.connect(this.audioContext.destination);
                    if (this.audioContext.state === 'suspended') {
                        void this.audioContext.resume();
                    }
                    this.beginSession();
                }
                catch (error) {
                    this.reportError(`Web Audio init failed: ${error}`);
                    void this.onCleanup();
                }
            },
            //MARK:cleanup
            cleanup() {
                try {
                    if (this.sourceNode) {
                        this.sourceNode.disconnect();
                    }
                }
                catch (_error) {
                }
                try {
                    if (this.processorNode) {
                        this.processorNode.disconnect();
                    }
                }
                catch (_error) {
                }
                try {
                    if (this.silentGainNode) {
                        this.silentGainNode.disconnect();
                    }
                }
                catch (_error) {
                }
                this.sourceNode = null;
                this.processorNode = null;
                this.silentGainNode = null;
            },
            //MARK:onCleanup
            async onCleanup() {
                this.clearRetry();
                this.cleanup();
                if (this.mediaStream) {
                    const allTracks = this.mediaStream.getTracks();
                    for (let index = 0; index < allTracks.length; index++) {
                        const currentTrack = allTracks[index];
                        try {
                            currentTrack.stop();
                        }
                        catch (_error) {
                            // pass
                        }
                    }
                }
                this.mediaStream = null;
                this.monitoredElement = null;
                this.channelCount = 1;
                this.sampleRate = 44100;
                this.isSessionActive = false;
                this.isStartPending = false;
                this.clearBuffer();
                if (this.audioContext) {
                    try {
                        await this.audioContext.close();
                    }
                    catch (_error) {
                        // pass
                    }
                }
                this.audioContext = null;
                this.strSessionId = null;
            },
            //==================================================
            // Public API
            //==================================================
            //MARK:startRecording
            startRecording() {
                this.isStartPending = true;
                this.checkBridge(() => {
                    this.monitor();
                });
            },
            //MARK:stopRecording
            stopRecording() {
                this.isStartPending = false;
                const sessionId = this.strSessionId;
                const bridge = this.bridge;
                this.isSessionActive = false;
                this.strSessionId = null;
                this.clearBuffer();
                if (bridge && sessionId) {
                    window.setTimeout(() => {
                        bridge.endRecord(sessionId);
                    }, 50);
                }
                void this.onCleanup();
            }
        };
        //==================================================
        // Initialize
        //==================================================
        window.shigeAudioRecorder = recorder;
        window.setTimeout(() => {
            recorder.monitor();
        }, 0);
    }
    //MARK:setup
    if (typeof QWebChannel !== 'undefined') {
        setupRecorder();
    }
})();
