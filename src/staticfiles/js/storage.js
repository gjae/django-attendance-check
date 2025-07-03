class IndexedDB {
    storage = null;
    storageIsOpen = false;
    objectStorage = null;
    db = null;
    _keyStorage = ""
    settings = {}

    constructor(storageName, version = 1) {
        this.storageName = storageName;
        this.version = version;
    }

    get storageDescription() {
        return `${this.storageName} (${this.version})`
    }

    get keyStorage (){ 
        return this._keyStorage;
    }

    setKeyStorage = (value, storageSettings) => {
        this._keyStorage = value
        this.settings = storageSettings
        if (this.db != null) {
            this.objectStorage = this.db.createObjectStore(this._keyStorage, storageSettings)
        }
    }

    init = (onsuccess, onerror, onupgradeneeded = null) => {
        /**
         * Inicializacion de la base de datos local e implementacion
         * de las llamadas de los eventos onsuccess y onerror
         */
        
        this.storage = window.indexedDB.open(
            this.storageName,
            this.version
        ) 
        this.bindEvents(onsuccess, onerror, onupgradeneeded)

    }

    setObjectStorage = (storageName) => {
        this._keyStorage = storageName
        try {
            this.objectStorage = this.db.transaction(this._keyStorage, "readwrite")
        } catch(e) {
            console.info("ERROR ", e)
        }
    }


    bindEvents = (onsuccess = null, onerror = null,  onupgradeneeded = null) => {
        if (typeof(this.storage) == "undefined" || this.storage == null) {
            throw new Error("Storage is not defined")
        }
        this.storage.onsuccess = (event) => {
            console.info(`${this.storageDescription} storage was opened succesfully`)
            this.storageIsOpen = true
            this.db = this.storage.result
            if (onsuccess !== null) {
                onsuccess(event, this)
            }
            
        }
        this.storage.onerror = (event) => {
            console.error(`${this.storageDescription} wasn't opened with error: `, event)
            this.storageIsOpen = false
            if (onerror !== null) {
                onerror(event)
            }
        }

        this.storage.onupgradeneeded = (event) => {
            this.db = event.target.result
            if (onupgradeneeded !== null) {
                onupgradeneeded(event, this)
            }
        }
    }


    insertElement = (elements = [], onsuccess = null) => {
        if (this.storageIsOpen) {
            
            const objectStorage = this.db.transaction(this._keyStorage, "readwrite").objectStore(this._keyStorage)
            elements.forEach((element) => {
                element["created"] = new Date()
                const addRequest =  objectStorage.add(element)
                addRequest.onsuccess = (event) => {
                    const result = event.target.result
                    if (onsuccess !== null) {
                        onsuccess(result)
                    } else {
                        console.info("New record has added ", result)
                    }
                }
            })
        }
    }

    all = (onsuccess) => {
        const transaction = this.db.transaction(this._keyStorage).objectStore(this._keyStorage)
        const request = transaction.openCursor(null, "prev")
        let res = new Array()
        console.log("CALLING ALL OBJECTS")
        request.onsuccess = (event) => {
            const cursor = event.target.result
            if (onsuccess == null) {
                console.info("Registros recuperados ", result)
                return
            }
            
            if (cursor) {
                res.push(cursor.value)
                cursor.continue()
            } else {
                onsuccess(res)
            }
        }
    }
}
