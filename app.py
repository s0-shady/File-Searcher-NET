from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import time
import tempfile
import shutil
from pathlib import Path

app = FastAPI(
    title="File Search API",
    description="API do wyszukiwania fraz w plikach tekstowych",
    version="1.0.0"
)

# Modele danych
class SearchRequest(BaseModel):
    start_path: str
    rozszerzenie: str = ".txt"
    fraza: str

class SearchResult(BaseModel):
    sciezka: str
    nr_linii: int
    tresc: str

class SearchResponse(BaseModel):
    wyniki: List[SearchResult]
    czas_wyszukiwania: str
    liczba_znalezionych: int
    status: str

# Twoja oryginalna funkcja - lekko zmodyfikowana
def czytelny_czas(sekundy):
    """Zamienia czas w sekundach na czytelną formę."""
    minuty, sekundy = divmod(int(sekundy), 60)
    godziny, minuty = divmod(minuty, 60)
    if godziny > 0:
        return f"{godziny} godz. {minuty} min {sekundy} sek"
    elif minuty > 0:
        return f"{minuty} minut i {sekundy} sekund"
    else:
        return f"{sekundy} sekund"

def przeszukaj_katalog(start_path, rozszerzenie, fraza):
    """Wyszukuje frazę w plikach - zmodyfikowana wersja bez printów."""
    znalezione = []
    
    if not os.path.exists(start_path):
        raise ValueError(f"Ścieżka nie istnieje: {start_path}")
    
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if file.endswith(rozszerzenie):
                sciezka = os.path.join(root, file)
                try:
                    with open(sciezka, 'r', encoding='utf-8', errors='ignore') as f:
                        for nr_linii, linia in enumerate(f, start=1):
                            if fraza in linia:
                                znalezione.append({
                                    "sciezka": sciezka,
                                    "nr_linii": nr_linii,
                                    "tresc": linia.strip()
                                })
                except Exception as e:
                    # W API logujemy błędy, ale nie przerywamy wyszukiwania
                    print(f"Błąd odczytu pliku {sciezka}: {e}")
                    continue
    
    return znalezione

# Endpoint główny - wyszukiwanie w istniejących plikach
@app.post("/search", response_model=SearchResponse)
async def search_files(request: SearchRequest):
    """
    Wyszukuje frazę w plikach w podanej ścieżce.
    
    - **start_path**: Ścieżka do katalogu do przeszukania
    - **rozszerzenie**: Rozszerzenie plików (np. .txt, .py)
    - **fraza**: Fraza do wyszukania
    """
    try:
        start_time = time.time()
        
        # Walidacja parametrów
        if not request.fraza.strip():
            raise HTTPException(status_code=400, detail="Fraza nie może być pusta")
        
        # Wyszukiwanie
        wyniki = przeszukaj_katalog(
            request.start_path, 
            request.rozszerzenie, 
            request.fraza
        )
        
        end_time = time.time()
        czas_wyszukiwania = czytelny_czas(end_time - start_time)
        
        return SearchResponse(
            wyniki=wyniki,
            czas_wyszukiwania=czas_wyszukiwania,
            liczba_znalezionych=len(wyniki),
            status="sukces"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd wewnętrzny: {str(e)}")

# Endpoint do wyszukiwania w uploadowanych plikach
@app.post("/search-uploaded", response_model=SearchResponse)
async def search_uploaded_files(
    fraza: str = Form(...),
    rozszerzenie: str = Form(".txt"),
    files: List[UploadFile] = File(...)
):
    """
    Wyszukuje frazę w uploadowanych plikach.
    
    - **fraza**: Fraza do wyszukania
    - **rozszerzenie**: Filtrowanie po rozszerzeniu (opcjonalne)
    - **files**: Pliki do przeszukania
    """
    try:
        start_time = time.time()
        wyniki = []
        
        # Tworzymy tymczasowy katalog
        with tempfile.TemporaryDirectory() as temp_dir:
            # Zapisujemy uploaded files
            for file in files:
                if file.filename.endswith(rozszerzenie) or rozszerzenie == "":
                    file_path = Path(temp_dir) / file.filename
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
            
            # Wyszukujemy w tymczasowym katalogu
            temp_wyniki = przeszukaj_katalog(temp_dir, rozszerzenie, fraza)
            
            # Zamieniamy ścieżki tymczasowe na nazwy plików
            for wynik in temp_wyniki:
                wynik["sciezka"] = os.path.basename(wynik["sciezka"])
                wyniki.append(wynik)
        
        end_time = time.time()
        czas_wyszukiwania = czytelny_czas(end_time - start_time)
        
        return SearchResponse(
            wyniki=wyniki,
            czas_wyszukiwania=czas_wyszukiwania,
            liczba_znalezionych=len(wyniki),
            status="sukces"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd przetwarzania plików: {str(e)}")

# Endpoint informacyjny
@app.get("/")
async def root():
    """Endpoint główny z informacjami o API."""
    return {
        "message": "File Search API",
        "version": "1.0.0",
        "endpoints": {
            "/search": "Wyszukiwanie w plikach na serwerze",
            "/search-uploaded": "Wyszukiwanie w uploadowanych plikach",
            "/docs": "Dokumentacja API"
        }
    }

# Endpoint healthcheck
@app.get("/health")
async def health_check():
    """Sprawdzanie statusu API."""
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Uruchamianie File Search API...")
    print("📚 Dokumentacja dostępna pod: http://localhost:8000/docs")
    print("🔍 API gotowe do wyszukiwania!")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)