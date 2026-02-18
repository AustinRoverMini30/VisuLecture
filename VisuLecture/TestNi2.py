import sys
import os
import numpy as np
import time
import pygame
import gc
import copy

from ButtonManager import ButtonManager
from staticData import *

# Ajout du dossier contenant les DLL au PATH Windows
DLL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../bin/win64'))
os.environ['PATH'] = DLL_PATH + os.pathsep + os.environ.get('PATH', '')
print(f"[DEBUG] DLL_PATH ajouté au PATH: {DLL_PATH}")
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

def generate_uniform_points(col, row, width=1920, height=1080, margin=0):
    points = []
    usable_width = width - 2 * margin
    for i in range(len(row)):
        for j in range(col):
            x = int(margin + (j + 0.5) * (usable_width / col))
            y = row[i]
            points.append(Point(i, x, y))

    return points

def main():
    calibrationIndex = 0

    global tobii_points


    screenSize = (1920, 1080)

    readingMode = True
    path = "Enregistrements/test"
    readingPoints = []

    tobii_points = []

    mots = pd.read_csv("resultats_ocr3.csv")

    # Résultat en liste [(ligne, y_global)]f
    listeY = getLinesList()
    pointsCalibrationInit = getReferencePoints()
    pointsCalibrationFinal = []

    if (readingMode):
        with open(f"{path}/points-bruts.csv", "r") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row
            for row in reader:
                if (len(row) > 3):
                    if not (isBlinking(row)):
                        readingPoints.append((float(row[0]), int(row[1]), int(row[2])))
                else:
                    readingPoints.append((float(row[0]), int(row[1]), int(row[2])))

        try:
            with open(f"{path}/points-tobii.csv", "r") as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header row
                for row in reader:
                    tobii_points.append(Point(float(row[0]), int(row[1]), int(row[2])))
        except Exception as e:
            tobii = False
            print(e)

        with open(f"{path}/points-calibration.csv", "r") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row
            for row in reader:
                pointsCalibrationFinal.append(Point(float(row[0]), int(row[1]), int(row[2])))

        my_eyetracker = None

    fenetre = pygame.display.set_mode(  )

    pygame.init()

    font = pygame.font.Font(None, 20)
    font1 = pygame.font.Font(None, 50)

    pygame.display.set_caption("VisuLecture : Experimental Box")

    pygame.draw.rect(fenetre, (0,0,0), (0,0,screenSize[0],screenSize[1]))

    pygame.draw.circle(fenetre, (255,255,255), (pointsCalibrationInit[calibrationIndex].x, pointsCalibrationInit[calibrationIndex].y), 20)

    pygame.display.flip()

    backgroundImage = pygame.image.load('lecture2.png')
    bouton = pygame.image.load('ON_OFF_maker.png')
    on_button = pygame.image.load('ON.png')
    off_button = pygame.image.load('OFF.png')


    fenetre.blit(backgroundImage, (0, 0))

    texte = font1.render("ESPACE pour lancer, puis pour arrêter", 1, (255, 0, 0))
    fenetre.blit(texte, (0, 0))

    pygame.display.flip()

    readingProcess = True

    while readingProcess and not(readingMode):
        for event in pygame.event.get():

            if event.type == pygame.KEYDOWN :

                if event.key == pygame.K_ESCAPE:
                    exit()

                if event.key == pygame.K_SPACE:
                    readingProcess = False

    fenetre.blit(backgroundImage, (0, 0))
    pygame.display.flip()

    if (my_eyetracker != None):
        my_eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)

    readingPoints = transformRawIntoPointsWithoutOperations(readingPoints)
    #readingPoints = recalibrateReadingWithOCR(readingPoints, getWordsPandas())
    readingPoints = getJumps(readingPoints, pointsCalibrationFinal, pointsCalibrationInit, 1920, 1080, len(listeY))
    #readingPoints = setPointsValues(readingPoints, pointsCalibrationFinal, pointsCalibrationInit)
    countJumps(readingPoints)
    pointsNormalized = normalizePoints(readingPoints, listeY)
    if not(readingMode):
        date = time.strftime("%Y%m%d-%H%M%S")
        os.makedirs(f"Enregistrements/{date}", exist_ok=True)
        path = f"Enregistrements/{date}/"

        record(readingPoints, path, "points-bruts", ["index", "x", "y"])
        record(pointsNormalized, path, "points-normalisés", ["index", "x", "y"])
        record(tobii_points, path, "points-tobii", ["index", "x", "y"])
        record(pointsCalibrationFinal, path, "points-calibration", ["index", "x", "y"])

    mots["has_point"] = False
    maxMot = len(mots)
    mots["nbMot"] = 0

    listeMots = extraire_durees_mots(mots, pointsNormalized)

    ButtonManager.path = path
    ButtonManager.createDataDictionnary()
    ButtonManager.updateData("points", readingPoints)
    ButtonManager("Points normalisés", (0,0,0), normalizePoints, lines=False)
    ButtonManager("Points bruts", (0,255,0), lambda: readingPoints, lines=False)
    ButtonManager("Chemins bruts", (0,150,0), lambda: readingPoints, lines=True)
    ButtonManager("Cacher sauts", None, ButtonManager.setHideJump, drawable=False, variableChangeButton=True)
    ButtonManager.updateData("fenetre", fenetre)
    ButtonManager.updateData("words", listeMots)
    ButtonManager.updateData("path", path)
    ButtonManager("Densité", None, ButtonManager.updateDensity, drawable=False, variableChangeButton=True)
    ButtonManager("Densite points norm", (150,0,25), normalizePoints, lines=True, densityLines=True)
    ButtonManager("Zones de regard (OLD)", (180, 70, 70), drawDensityCircles, drawable=False)
    ButtonManager("Chemins calibrés (NEW)", (155,140,210), drawCalibratedLinesNew)
    ButtonManager("PolyDeg3", (150, 10, 10), drawCalibratedLinesPoly3)
    ButtonManager("Affine", (0,180,50), drawCalibratedLinesAffine)
    ButtonManager("Homography",(225,140,87), drawCalibratedLinesHomography)
    ButtonManager("Calibation", (230,230,110), showCalibrationPoints, drawable=False)
    ButtonManager("Calibration Coeff", (255,0,98), calcCalibratedLinesCoef)
    ButtonManager("Calibration Coeff v2", (255,170,0), calcCalibratedLinesCoef2)
    ButtonManager("Smooth calibration", (0,8,190), calcCalibratedLinesCoefSmooth)
    ButtonManager("Turbo Smooth", (0,255,0), calcTurboSmooth)
    ButtonManager("Smooth of the smooths", (240,240,15), averageSmooth)
    ButtonManager("The ultimate method", (144,144,144), ultimateSmooth)
    ButtonManager("Points normalisés USmooth", (144, 144, 144), normalizePoints, lines=False, instanceDict={"points" : ultimateSmooth(fenetre, readingPoints, pointsCalibrationFinal, pointsCalibrationInit, 1920, 1080, listeY)})
    ButtonManager("Zones de regard USmooth", (144, 144, 144), drawDensityCircles, drawable=False, instanceDict={"words": extraire_durees_mots(mots, normalizePoints(ultimateSmooth(fenetre, readingPoints, pointsCalibrationFinal, pointsCalibrationInit, 1920, 1080, listeY), listeY))})
    ButtonManager("Hitbox Mots", (240,240,15), drawRect, drawable=False)
    ButtonManager("Capture d'écran", None, ButtonManager.captureScreen, drawable=False, variableChangeButton=True)
    ButtonManager("Quadrilatère lecture", None, drawReadingQuad, drawable=False)
    ButtonManager("Quadrilatère adjusted", None, drawReadingQuadFiltered, drawable=False)
    ButtonManager("Quadrilatère Mots", None, drawWordsQuad, drawable=False, instanceDict={"words": getWordsPandas()})
    ButtonManager("Homographie box", (15,180,190), recalibrateReadingWithOCR, lines=True   , instanceDict={"words": getWordsPandas()})
    ButtonManager("Homographie + snap", (255,255,14), adjust_lines, lines=True, instanceDict={"points": recalibrateReadingWithOCR(readingPoints, getWordsPandas(), listeY)})
    ButtonManager("Homographie + snap", (255,15,180), adjust_lines, lines=False, instanceDict={"points": recalibrateReadingWithOCR(readingPoints, getWordsPandas(), listeY)})
    ButtonManager("Zones de regard (OLD)",  (180, 70, 70), drawDensityCircles, drawable=False, instanceDict={"words": extraire_durees_mots(mots, normalizePoints(recalibrateReadingWithOCR(readingPoints, getWordsPandas(), listeY), getLinesList()))    })

    ButtonManager.createButtons(fenetre, bouton, font, backgroundImage, off_button=off_button, on_button=on_button)

    while (True):
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if (ButtonManager.createEvent(event.pos)):
                    ButtonManager.createButtons(fenetre, bouton, font, backgroundImage, off_button=off_button, on_button=on_button)

            if event.type == pygame.KEYDOWN :
                if event.key == pygame.K_ESCAPE:
                    exit()

def setPointsValues(points):
    """
    Marque les objets Point selon la détection de saut (jump).
    Ne fait plus aucune conversion ni traitement de clignement.

    points : liste d’objets Point
    """
    listePoints = []

    if len(points) > 1:
        n = len(points) - 1
        i = 0

        while i < n:
            # détection du saut entre le point courant et les suivants
            jump, skip, _ = isJump(points[i], points[(i + 1):])

            if not jump:
                # point normal (pas de saut)
                listePoints.append(Point(points[i].timestamp, points[i].x, points[i].y, False))
                i += 1
            else:
                # points appartenant au saut
                for j in range(i + 1, i + 1 + skip):
                    if j >= len(points):
                        break
                    listePoints.append(Point(points[j].timestamp, points[j].x, points[j].y, True))
                i += skip
    else:
        # un seul point -> pas de saut possible
        p = points[0]
        listePoints.append(Point(p.timestamp, p.x, p.y, False))

    return listePoints



def drawLines(fenetre, color, points, hideJump=False, jumpVal=300, density=False):
    for i in range(len(points)-1):

        if (density):
            distance = distBetweenPoints(points[i], points[i + 1])
            if (distance > 40):
                width = 1
            else:
                width = 10

        else:
            width = 3

        if points[i].jump and not hideJump:
            pygame.draw.line(fenetre, (0,0,255), points[i].coord(), points[i+1].coord(), width)

        if not points[i].jump:
            pygame.draw.line(fenetre, color, points[i].coord(), points[i+1].coord(), width)

def drawPoints(fenetre, color, points, hideJump=False, jumpVal=300):
    if len(points) > 1:
        for i in range(len(points)):
            pygame.draw.circle(fenetre, color, (points[i].x, points[i].y), 5)

def showCalibrationPoints(fenetre, reference, calibration):
    print("Calibration size ", len(calibration))
    print("reference size ", len(reference))


    for i in range(len(reference)):
        pygame.draw.circle(fenetre, (0, 0, 255), (reference[i].x, reference[i].y), 20, 4)
        pygame.draw.circle(fenetre, (255, 0, 0), (calibration[i].x, calibration[i].y), 10)
        pygame.draw.line(fenetre, (255, 0, 255), (reference[i].x, reference[i].y), (calibration[i].x, calibration[i].y), 2)

def normalizePoints(points, listeY, min_dx=-30, min_ratio=0.7, min_gap=80):
    jump = False
    ligne = 0
    listePointsNormalized = []
    for i in range(len(points)):
        if (points[i].jump):
            jump = True

        if jump and not(points[i].jump):
            ligne += 1
            jump = False

        if not points[i].jump:
            listePointsNormalized.append(Point(points[i].timestamp, points[i].x, listeY[ligne], points[i].jump))

    return listePointsNormalized

def distBetweenPoints(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def isJump(current_point, next_points, min_dx=-50, min_ratio=0.7, min_gap=800):
    """
    Détecte un retour à la ligne sur l’axe X uniquement.

    Renvoie :
        - is_jump (bool): True si un retour de ligne est détecté
        - skip_count (int): nombre de points à sauter pour arriver au début de la nouvelle ligne
        - idx_newline (int): index relatif du point où la reprise de ligne commence

    current_point : objet Point courant
    next_points   : liste d’objets Point suivants
    """

    next_points = next_points[:31]

    if not next_points:
        return False, 0, None

    # si le premier point suivant est à droite (pas de retour)
    if next_points[0].x > current_point.x:
        return False, 0, None

    x0 = current_point.x
    y0 = current_point.y


    x_last = next_points[0].x
    y_last = next_points[0].y
    for elem in next_points[1:]:
        if x_last > elem.x:
            x_last = elem.x

        if y_last < elem.y:
            y_last = elem.y

    # mouvement global sur X
    global_dx = x_last - x0

    # proportion de points qui sont à gauche du point courant
    left_moves = sum(1 for p in next_points if p.x < x0)
    ratio_left = left_moves / len(next_points)

    # détection du saut
    if global_dx < min_dx and ratio_left >= min_ratio:
        min_x = float("inf")
        idx_newline = None

        for i, p in enumerate(next_points):
            if p.x < min_x:
                min_x = p.x
            # quand on revient à droite après un minimum (reprise de ligne)
            if p.x > min_x + 5:  # tolérance au bruit
                idx_newline = i
                break

        if idx_newline is None:
            idx_newline = len(next_points) - 1


        print(y0, y_last)
        # vérifie que le retour est suffisamment grand pour être un saut
        if ((x0 - min_x) >= min_gap) and y0+150 < y_last:
            return True, idx_newline + 1, idx_newline

    return False, 0, None

def isJumpNew(currentPoint, nextPoints, coeffCalibration, nbLines, averageReadingSpeed, moyenneCoeff, height_coef, width_coef, fps=30, width=1920, height=1080):
    def compute_speeds(points):
        speeds = []
        for i in range(1, len(points)):
            dx = points[i].x - points[i-1].x
            dy = points[i].y - points[i-1].y
            dist = (dx**2 + dy**2)**0.5
            speeds.append(dist)
        return speeds

    def compute_accelerations(speeds):
        return [speeds[i] - speeds[i-1] for i in range(1, len(speeds))]

    if (len(nextPoints) > 1 and average_speed([currentPoint, nextPoints[1]]) < 1000):
        return False, 0

    if moyenneCoeff < 150:
        authorized_interval_coeff = 1
    else:
        authorized_interval_coeff = 150 / moyenneCoeff
    for interval_size in range(int(fps / 4), int(fps / 1.5)):
        interval_points = nextPoints[:interval_size]
        if not interval_points:
            continue  # sécurité de base


        min_x = float("inf")
        index = 0
        globalIndex = 0
        for p in interval_points:
            globalIndex += 1
            if (p.x < min_x):
                min_x = p.x
                index = globalIndex

        end_point = len(interval_points)  # par défaut, on garde tout
        #Permet de tronquer la liste et s'arrête quand on va vers la droite
        for j, point in enumerate(interval_points):
            if point.x > min_x + 5 and j > index:
                new_length = j
                break
        interval_points = interval_points[:end_point]

        if len(interval_points) <= 2:
            continue

        first_point = interval_points[0]
        last_point = interval_points[-1]
        avg_speed = average_speed(interval_points)
        if avg_speed < 1000:
            continue
        if last_point.x >= 0.5 * width:
            continue

        if (last_point.x + int(500 * authorized_interval_coeff * width_coef)) < first_point.x and last_point.y > first_point.y + int(65 * authorized_interval_coeff * height_coef):
            # --- New acceleration spike detection ---
            speeds = compute_speeds(interval_points)
            accelerations = compute_accelerations(speeds)
            if accelerations:
                max_acc = max(accelerations)
                min_acc = min(accelerations)
                # Thresholds are empirical — adjust via calibration
                if abs(max_acc - min_acc) < averageReadingSpeed * 2:
                    return True, interval_size
    return False, 0

def average_speed(nextPoints, fps=30):
    if len(nextPoints) < 2:
        return 0.0

    distances = []
    for i in range(len(nextPoints) - 1):
        p1 = nextPoints[i]
        p2 = nextPoints[i + 1]
        dist = math.hypot(p2.x - p1.x, p2.y - p1.y)  # distance euclidienne
        distances.append(dist)

    mean_dist_per_frame = sum(distances) / len(distances)
    mean_speed_per_second = mean_dist_per_frame * fps
    return mean_speed_per_second  # ou mean_dist_per_frame selon ton besoin

def drawDensityCircles(words, fenetre):

    for (x, y, d) in words:
        radius = int(d * 100)
        if radius < 10:
            radius = 10
        elif radius > 100:
            radius = 100
        # Création d'une surface temporaire avec transparence
        circle_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, (0, 0, 255, 100), (radius, radius), radius)
        fenetre.blit(circle_surface, (int(x)-radius, int(y)-radius))


def record(points, path, nom, header):
    with open(f"{path}/{nom}.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for elem in points:
            writer.writerow(elem.getTuple())

def lire_resultats_ocr(path_csv):
    """
    Lit le fichier resultats_ocr.csv et retourne une liste de dictionnaires.
    Chaque dictionnaire correspond à une ligne du fichier.
    """
    resultats = []
    with open(path_csv, newline='', encoding='utf-8') as csvfile:
        lecteur = csv.DictReader(csvfile)
        for ligne in lecteur:
            # Conversion des champs numériques
            ligne['x'] = int(ligne['x'])
            ligne['y'] = int(ligne['y'])
            ligne['largeur'] = int(ligne['largeur'])
            ligne['hauteur'] = int(ligne['hauteur'])
            ligne['ligne'] = int(ligne['ligne'])
            ligne['confiance'] = int(ligne['confiance'])
            resultats.append(ligne)
    return resultats

def gaze_data_callback(gaze_data):
    global tobii_points

    screen_width = 1920
    screen_height = 1080

    timestamp = gaze_data['system_time_stamp']
    left_norm = gaze_data['left_gaze_point_on_display_area']
    right_norm = gaze_data['right_gaze_point_on_display_area']

    valid_left = left_norm[0] >= 0 and left_norm[1] >= 0
    valid_right = right_norm[0] >= 0 and right_norm[1] >= 0

    if valid_left and valid_right:
        x = (left_norm[0] + right_norm[0]) / 2 * screen_width
        y = (left_norm[1] + right_norm[1]) / 2 * screen_height
        tobii_points.append(Point(timestamp, int(x), int(y)))
    elif valid_left:
        x, y = left_norm[0] * screen_width, left_norm[1] * screen_height
        tobii_points.append(Point(timestamp, int(x), int(y)))
    elif valid_right:
        x, y = right_norm[0] * screen_width, right_norm[1] * screen_height
        tobii_points.append(Point(timestamp, int(x), int(y)))
    else:
        print("No valid gaze data")

def isBlinking(point):
    return True

def drawCalibratedLinesNew(calibration, reference, points):

    new_points = calibrate_and_transform_points_for_any_calibration_points(calibration, reference, points)
    new_points = calibrate_and_transform_polynomial(calibration, reference, new_points)
    return new_points

def drawCalibratedLinesPoly3(calibration, reference, points):
    new_points = calibrate_and_transform_points_for_any_calibration_points(calibration, reference, points)
    new_points = calibrate_and_transform_polynomial_deg3(calibration, reference, new_points)

    return new_points

def drawCalibratedLinesAffine(calibration, reference, points):
    new_points = calibrate_and_transform_points_for_any_calibration_points(calibration, reference, points)
    return new_points

def drawCalibratedLinesHomography(calibration, reference, points):
    new_points = calibrate_and_transform_homography(calibration, reference, points)
    return new_points

def calcCalibratedLinesCoef(fenetre, calibration, reference, points, width, height):
    coef = []
    coefTmp = []

    last = reference[0].y  # On prend la première valeur Y de référence comme base

    newList = []

    # Construction de la grille de coefficients (par ligne)
    for i in range(len(reference)):
        if last != reference[i].y:
            last = reference[i].y
            if coefTmp:
                coef.append(coefTmp)
                coefTmp = []

        # coefTmp est une ligne (liste des colonnes pour une ligne donnée)
        coefTmp.append((reference[i].x - calibration[i].x,
                        reference[i].y - calibration[i].y))
    coef.append(coefTmp)  # On ajoute la dernière ligne

    n_rows = len(coef)          # Nombre de lignes
    n_cols = len(coef[0])       # Nombre de colonnes

    for i in range(len(points)):
        x, y = points[i].x, points[i].y

        # Détermination de la colonne
        if x < 0:
            col = 0
        elif x >= width:
            col = n_cols - 1
        else:
            col = int(x // (width / n_cols))

        # Détermination de la ligne
        if y < 0:
            ligne = 0
        elif y >= height:
            ligne = n_rows - 1
        else:
            ligne = int(y // (height / n_rows))

        try:
            dx, dy = coef[ligne][col]
            newList.append(Point(points[i].timestamp, points[i].x + dx, points[i].y + dy, points[i].jump))
        except Exception as e:
            print(f"[ERREUR] Point {i}: ({x}, {y}) -> Cellule ({ligne}, {col}), hors grille ? {e}")

    return newList

def calcCalibratedLinesCoef2(fenetre, calibration, reference, points, width, height):
    coef = []
    coefTmp = []

    coefEquivalent = []
    coefEquivalentTmp = []

    last = reference[0].y  # On prend la première valeur Y de référence comme base

    newList = []

    # Construction de la grille de coefficients (par ligne)
    for i in range(len(reference)):
        if last != reference[i].y:
            last = reference[i].y
            if coefTmp:
                coef.append(coefTmp)
                coefTmp = []

                coefEquivalent.append(coefEquivalentTmp)
                coefEquivalentTmp = []

        # coefTmp est une ligne (liste des colonnes pour une ligne donnée)
        coefTmp.append((reference[i].x - calibration[i].x,
                        reference[i].y - calibration[i].y))

        coefEquivalentTmp.append((calibration[i].x, calibration[i].y))
    coef.append(coefTmp)  # On ajoute la dernière ligne
    coefEquivalent.append(coefEquivalentTmp)  # On ajoute la dernière ligne

    n_rows = len(coef)          # Nombre de lignes
    n_cols = len(coef[0])       # Nombre de colonnes

    for i in range(len(points)):
        x, y = points[i].x, points[i].y

        minimum = 1920*1080
        choice = None

        for ligne in range(len(coefEquivalent)):
            for col in range(len(coefEquivalent[0])):

                if (minimum > distBetweenPoints(points[i], Point(0, coefEquivalent[ligne][col][0], coefEquivalent[ligne][col][1], False))):
                    minimum = distBetweenPoints(points[i], Point(0, coefEquivalent[ligne][col][0], coefEquivalent[ligne][col][1], False))
                    choice = (ligne, col)

        dx, dy = coef[choice[0]][choice[1]]
        newList.append(Point(points[i].timestamp, points[i].x + dx, points[i].y + dy, points[i].jump))

    return newList

import math

def calcCalibratedLinesCoefSmooth(fenetre, calibration, reference, points, width, height, radius=200):
    """
    Version lissée de la calibration :
    - Calcule les décalages dx, dy entre calibration et référence
    - Applique un lissage local (pondération par distance^2)
    - radius : rayon d'influence en pixels
    """

    # Construction de la grille des coefficients (dx, dy)
    coef = []
    coefTmp = []
    last_y = reference[0].y

    for i in range(len(reference)):
        if reference[i].y != last_y:
            last_y = reference[i].y
            if coefTmp:
                coef.append(coefTmp)
                coefTmp = []

        dx = reference[i].x - calibration[i].x
        dy = reference[i].y - calibration[i].y
        coefTmp.append((calibration[i].x, calibration[i].y, dx, dy))

    coef.append(coefTmp)  # dernière ligne
    all_points = [p for row in coef for p in row]  # pour recherche globale

    newList = []

    for i, p in enumerate(points):
        x, y = p.x, p.y

        weighted_dx = 0.0
        weighted_dy = 0.0
        total_weight = 0.0

        # On ne prend en compte que les points de calibration dans un certain rayon
        for cx, cy, dx, dy in all_points:
            dist2 = (x - cx) ** 2 + (y - cy) ** 2
            if dist2 < radius ** 2 and dist2 > 0:
                # Poids inversement proportionnel à la distance au carré
                w = 1 / dist2
                weighted_dx += dx * w
                weighted_dy += dy * w
                total_weight += w

        if total_weight > 0:
            avg_dx = weighted_dx / total_weight
            avg_dy = weighted_dy / total_weight
        else:
            # Aucun voisin proche : on cherche le plus proche (fallback)
            nearest = min(all_points, key=lambda c: (x - c[0]) ** 2 + (y - c[1]) ** 2)
            avg_dx, avg_dy = nearest[2], nearest[3]

        newList.append(Point(p.timestamp, p.x + avg_dx, p.y + avg_dy, p.jump))

    return newList



def build_coef(calibration, reference):
    """Construit la grille des coefficients à partir des points de calibration."""
    coef, coefTmp = [], []
    last_y = reference[0].y
    for i in range(len(reference)):
        if reference[i].y != last_y:
            coef.append(coefTmp)
            coefTmp = []
            last_y = reference[i].y

        dx = reference[i].x - calibration[i].x
        dy = reference[i].y - calibration[i].y
        coefTmp.append((dx, dy))

    coef.append(coefTmp)
    return coef


def calcTurboSmooth(fenetre, calibration, reference, points, width, height, radius_cells=1, precomputed_coef=None):
    """
    Version optimisée et mémoire-sûre :
    - Lissage 1 / distance²
    - Nettoyage automatique mémoire temporaire
    - Possibilité de réutiliser une grille `coef` déjà calculée (precomputed_coef)
    """
    # Utilise un coef déjà construit si fourni
    coef = precomputed_coef or build_coef(calibration, reference)
    n_rows = len(coef)
    n_cols = len(coef[0])

    cell_w = width / n_cols
    cell_h = height / n_rows

    # Pré-calcul des centres de cellules (pour éviter de recalculer cx/cy à chaque point)
    cell_centers = [
        [( (c + 0.5) * cell_w, (l + 0.5) * cell_h ) for c in range(n_cols)]
        for l in range(n_rows)
    ]

    new_points = []
    radius = range(-radius_cells, radius_cells + 1)

    for p in points:
        x, y = p.x, p.y

        # Détermination de la cellule
        col = int(min(max(x, 0), width - 1) // cell_w)
        row = int(min(max(y, 0), height - 1) // cell_h)

        weighted_dx = 0.0
        weighted_dy = 0.0
        total_w = 0.0

        # Boucle sur les cellules voisines
        for dy_i in radius:
            r = row + dy_i
            if 0 <= r < n_rows:
                for dx_i in radius:
                    c = col + dx_i
                    if 0 <= c < n_cols:
                        dx, dy = coef[r][c]
                        cx, cy = cell_centers[r][c]

                        dist2 = (x - cx)**2 + (y - cy)**2
                        if dist2 == 0:
                            dist2 = 1e-6
                        w = 1.0 / dist2

                        weighted_dx += dx * w
                        weighted_dy += dy * w
                        total_w += w

        if total_w > 0:
            avg_dx = weighted_dx / total_w
            avg_dy = weighted_dy / total_w
        else:
            avg_dx, avg_dy = coef[row][col]

        new_points.append(Point(p.timestamp, p.x + avg_dx, p.y + avg_dy, p.jump))

    # Nettoyage mémoire
    del coef, cell_centers
    gc.collect()

    return new_points

def averageSmooth(fenetre, calibration, reference, points, width, height, radius=200):

    turboSmooth = calcTurboSmooth(fenetre,calibration,reference,points,width,height,radius)

    calibratedSmooth = calcCalibratedLinesCoefSmooth(fenetre,calibration,reference,points,width,height,radius)
    pts = averageFromOther([turboSmooth, calibratedSmooth])
    return pts
def drawCalibratedLinesCoef(fenetre, calibration, reference, points, hideJump=False, jumpVal=300, density=False):
    new_points = calcCalibratedLinesCoef(fenetre, calibration, reference, points, 1920, 1080)

    drawLines(fenetre, (0, 255, 0), new_points, hideJump, density=density)

def drawCalibratedLinesCoef2(fenetre, calibration, reference, points, hideJump=False, jumpVal=300, density=False):
    new_points = calcCalibratedLinesCoef2(fenetre, calibration, reference, points, 1920, 1080)
    new_points = calibrate_and_transform_polynomial_deg3(calibration, reference, new_points)

    drawLines(fenetre, (0, 255, 0), new_points, hideJump, density=density)

def drawCalibratedLinesAffineCoef(fenetre, calibration, reference, points, hideJump=False, jumpVal=300, density=False):
    new_points = calcCalibratedLinesCoef(fenetre, calibration, reference, points, 1920, 1080)
    new_points = calibrate_and_transform_points_for_any_calibration_points(calibration, reference, new_points)

    drawLines(fenetre, (0, 255, 0), new_points, hideJump, density=density)

def drawCalibrateFromOtherProcess(fenetre, calibration, reference, points, hideJump=False, jumpVal=300, density=False):

    liste1 = calcCalibratedLinesCoef(fenetre, calibration, reference, points, 1920, 1080)
    liste2 = calcCalibratedLinesCoef2(fenetre, calibration, reference, points, 1920, 1080)
    liste3 = calcCalibratedLinesCoef(fenetre, calibration, reference, points, 1920, 1080)
    liste3 = calibrate_and_transform_points_for_any_calibration_points(calibration, reference, liste3)


    new_points = averageFromOther([liste1, liste2, liste3])

    drawLines(fenetre, (0, 255, 0), new_points, hideJump, density=density)

def averageFromOther(liste):
    """
    Calcule la moyenne des coordonnées X/Y de plusieurs séries de points.
    Chaque sous-liste dans `liste` doit avoir la même longueur.
    Retourne une nouvelle liste de Points moyennés.
    """
    if not liste or not liste[0]:
        return []

    n_series = len(liste)
    n_points = len(liste[0])
    new_points = []

    for i in range(n_points):
        # Récupère tous les points à l'indice i dans chaque série
        points_i = [serie[i] for serie in liste]

        # Moyenne des coordonnées
        avg_x = sum(p.x for p in points_i) / n_series
        avg_y = sum(p.y for p in points_i) / n_series

        # On reprend timestamp et jump du premier (supposés identiques)
        new_points.append(Point(points_i[0].timestamp, int(avg_x), int(avg_y), points_i[0].jump))

    return new_points

def calibrate_and_transform_points_for_any_calibration_points(eye_points_idx, screen_points_idx, new_points_idx):
    """
    Calibre une transformation affine 2D à partir de tuples (idx, x, y) et
    l'applique à de nouveaux points (idx, x, y).

    :param eye_points_idx: [(i, x, y), ...]  mesures brutes (œil) pour la calibration
    :param screen_points_idx: [(i, x', y'), ...] positions écran correspondantes
    :param new_points_idx: [(i, x, y), ...] nouveaux points à transformer
    :return: [(i, x', y'), ...] nouveaux points transformés avec le même idx
    """
    # ---- 1) Extraire x,y en ignorant idx ----
    eye = np.array([(tmp.x, tmp.y) for tmp in eye_points_idx], dtype=float)  # (N,2)
    screen = np.array([(elem.x, elem.y) for elem in screen_points_idx], dtype=float)  # (N,2)
    N = eye.shape[0]
    if N < 3:
        raise ValueError("Au moins 3 correspondances (idx,x,y) sont nécessaires pour une affine 2D.")

    # ---- 2) Construire le système A θ = b ----
    # θ = [a, b, c, d, tx, ty]^T
    A = np.zeros((2 * N, 6), dtype=float)
    b = np.zeros((2 * N,), dtype=float)
    for i, (x, y) in enumerate(eye):
        # x' = a x + b y + tx
        A[2 * i, 0] = x
        A[2 * i, 1] = y
        A[2 * i, 4] = 1.0
        b[2 * i] = screen[i, 0]
        # y' = c x + d y + ty
        A[2 * i + 1, 2] = x
        A[2 * i + 1, 3] = y
        A[2 * i + 1, 5] = 1.0
        b[2 * i + 1] = screen[i, 1]

    # ---- 3) Estimer les paramètres par moindres carrés ----
    theta, *_ = np.linalg.lstsq(A, b, rcond=None)
    a, b_, c, d, tx, ty = theta

    # ---- 4) Transformer les nouveaux points (en conservant idx) ----
    if len(new_points_idx) == 0:
        return []

    new_xy = np.array([(elem.x, elem.y) for elem in new_points_idx], dtype=float)  # (M,2)
    x = new_xy[:, 0];
    y = new_xy[:, 1]
    x_p = a * x + b_ * y + tx
    y_p = c * x + d * y + ty

    # Retourne [(idx, x', y')]
    out = [Point(elem.timestamp, float(xp), float(yp), elem.jump) for elem, xp, yp in zip(new_points_idx, x_p, y_p)]

    return out

def calibrate_and_transform_homography(eye_points_idx, screen_points_idx, new_points_idx):
    """
    Calibre une transformation homographique (2D projective) et l’applique à de nouveaux points.
    :param eye_points_idx: [(i, x, y), ...] points bruts
    :param screen_points_idx: [(i, x', y'), ...] points écran
    :param new_points_idx: [(i, x, y), ...] points à transformer
    :return: [(i, x', y'), ...] points transformés
    """
    eye = np.array([(tmp.x, tmp.y) for tmp in eye_points_idx], dtype=float)
    screen = np.array([(elem.x, elem.y) for elem in screen_points_idx], dtype=float)
    N = eye.shape[0]
    if N < 4:
        raise ValueError("Il faut au moins 4 points pour une homographie.")

    # Construction du système A h = 0
    A = []
    for (x, y), (xp, yp) in zip(eye, screen):
        A.append([x, y, 1, 0, 0, 0, -xp * x, -xp * y, -xp])
        A.append([0, 0, 0, x, y, 1, -yp * x, -yp * y, -yp])
    A = np.array(A)

    # Résolution par SVD (vecteur propre associé à la plus petite valeur singulière)
    U, S, Vt = np.linalg.svd(A)
    h = Vt[-1, :] / Vt[-1, -1]  # normaliser
    H = h.reshape(3, 3)

    # Transformation des nouveaux points
    out = []
    for elem in new_points_idx:
        vec = np.array([elem.x, elem.y, 1.0])
        xp, yp, w = H @ vec
        out.append(Point(elem.timestamp, float(xp / w), float(yp / w), elem.jump))
    return out


def calibrate_and_transform_polynomial(eye_points_idx, screen_points_idx, new_points_idx):
    """
    Calibre un modèle polynomial quadratique 2D et applique à de nouveaux points.
    :param eye_points_idx: [(i, x, y), ...]
    :param screen_points_idx: [(i, x', y'), ...]
    :param new_points_idx: [(i, x, y), ...]
    :return: [(i, x', y'), ...]
    """
    eye = np.array([(tmp.x, tmp.y) for tmp in eye_points_idx], dtype=float)
    screen = np.array([(elem.x, elem.y) for elem in screen_points_idx], dtype=float)
    N = eye.shape[0]
    if N < 6:
        raise ValueError("Il faut au moins 6 points pour un modèle polynomial quadratique.")

    # Construction de la matrice de régression (design matrix)
    X = np.column_stack([
        np.ones(N),
        eye[:, 0],  # x
        eye[:, 1],  # y
        eye[:, 0] ** 2,  # x^2
        eye[:, 0] * eye[:, 1],  # xy
        eye[:, 1] ** 2  # y^2
    ])

    # Moindres carrés pour x' et y'
    coeffs_x, *_ = np.linalg.lstsq(X, screen[:, 0], rcond=None)
    coeffs_y, *_ = np.linalg.lstsq(X, screen[:, 1], rcond=None)

    # Transformer de nouveaux points
    out = []
    for elem in new_points_idx:
        vec = np.array([1, elem.x, elem.y, elem.x ** 2, elem.x * elem.y, elem.y ** 2])
        xp = coeffs_x @ vec
        yp = coeffs_y @ vec
        out.append(Point(elem.timestamp, float(xp), float(yp), elem.jump))
    return out

def _design_matrix_deg3(xy: np.ndarray) -> np.ndarray:
    x = xy[:, 0]
    y = xy[:, 1]
    return np.column_stack([
        np.ones_like(x),  # 1
        x,                # x
        y,                # y
        x**2,             # x^2
        x*y,              # xy
        y**2,             # y^2
        x**3,             # x^3
        (x**2)*y,         # x^2 y
        x*(y**2),         # x y^2
        y**3              # y^3
    ])  # (N, 10)


def calibrate_and_transform_polynomial_deg3(eye_points_idx, screen_points_idx, new_points_idx):
    """
    Calibre un modèle polynomial 2D de degré 3 et l'applique à de nouveaux points.
    Entrées/sortie au format [(idx, x, y), ...].

    Besoin de >= 10 points (10 paramètres par axe, 20 au total).
    Retourne : [(idx, x', y'), ...] pour les new_points_idx.
    """
    eye = np.array([(tmp.x, tmp.y) for tmp in eye_points_idx], dtype=float)  # (N,2)
    screen = np.array([(elem.x, elem.y) for elem in screen_points_idx], dtype=float)  # (N,2)
    N = eye.shape[0]
    if N < 10:
        raise ValueError("Il faut au moins 10 points pour un polynôme 2D de degré 3.")

    # Matrice de régression (design)
    X = _design_matrix_deg3(eye)  # (N,10)

    # Moindres carrés indépendants pour x' et y'
    coeffs_x, *_ = np.linalg.lstsq(X, screen[:, 0], rcond=None)  # (10,)
    coeffs_y, *_ = np.linalg.lstsq(X, screen[:, 1], rcond=None)  # (10,)

    # Transformer les nouveaux points
    if len(new_points_idx) == 0:
        return []

    new_xy = np.array([(elem.x, elem.y) for elem in new_points_idx], dtype=float)  # (M,2)
    X_new = _design_matrix_deg3(new_xy)  # (M,10)

    x_pred = X_new @ coeffs_x
    y_pred = X_new @ coeffs_y

    out = [Point(elem.timestamp, float(xp), float(yp), elem.jump) for elem, xp, yp in zip(new_points_idx, x_pred, y_pred)]
    return out


def _build_norm_index_map(points):
    """
    Construit un mapping index_original -> index_normalisé (ou None si jump=True).
    L'index dans la liste normalisée compte uniquement les points non-jump.
    """
    idx_map = []
    c = 0
    for p in points:
        if p.jump:
            idx_map.append(None)
        else:
            idx_map.append(c)
            c += 1
    return idx_map  # longueur = len(points)

def _mean_euclidean_error_window(points, norm_points, idx_map, start, end):
    """
    Erreur euclidienne moyenne entre points[start:end] et norm_points,
    en ne comptant que les points non-jump (ceux qui existent dans norm_points).
    Retourne None si aucun point comparable dans la fenêtre.
    """
    s = 0.0
    k = 0
    for i in range(start, end):
        j = idx_map[i]
        if j is None:
            continue
        # j indexe norm_points (qui ne contient que des non-jump)
        p = points[i]
        n = norm_points[j]
        dx = p.x - n.x
        dy = p.y - n.y
        s += math.hypot(dx, dy)
        k += 1
    if k == 0:
        return None
    return s / k

def _window_slices(n, window_size):
    return [(i, min(i + window_size, n)) for i in range(0, n, window_size)]

def blend_points_by_error(points_a, points_b, listeY, window_size=75, epsilon=1e-12):
    """
    Mélange deux listes de Point (A et B) par fenêtres de `window_size`.
    Pondération inverse au **carré** de l'erreur moyenne calculée
    entre chaque série et sa version normalisée (qui retire les points jump).

    - L'erreur d'une fenêtre est calculée uniquement sur les points non-jump
      (ceux présents dans la liste normalisée), avec l'alignement via un mapping.
    - Si une fenêtre ne contient aucun point comparable pour A ou B:
        * si les deux sont vides -> poids 0.5 / 0.5
        * si un seul a des points -> poids 1.0 pour celui-ci
    - On pondère x,y par ces poids; pour `jump`, on reprend la valeur
      de la méthode dominante sur la fenêtre (à égalité: True si l’un est True).
    - La fonction renvoie uniquement la liste fusionnée.
    """
    if len(points_a) != len(points_b):
        raise ValueError("points_a et points_b doivent avoir la même longueur.")
    n = len(points_a)
    if n == 0:
        return []

    # Normalisations propres à chaque série (les jumps peuvent différer entre A et B)
    norm_a = normalizePoints(points_a, listeY)
    norm_b = normalizePoints(points_b, listeY)

    # Mappings index original -> index normalisé (ou None si jump)
    idx_map_a = _build_norm_index_map(points_a)
    idx_map_b = _build_norm_index_map(points_b)

    blended = []

    for start, end in _window_slices(n, window_size):
        # Erreurs moyennes par fenêtre (None si aucun point comparable)
        err_a = _mean_euclidean_error_window(points_a, norm_a, idx_map_a, start, end)
        err_b = _mean_euclidean_error_window(points_b, norm_b, idx_map_b, start, end)

        # Poids inverse au carré de l'erreur, avec cas dégénérés gérés
        if err_a is None and err_b is None:
            w_a, w_b = 0.5, 0.5
        elif err_a is None:
            w_a, w_b = 0.0, 1.0
        elif err_b is None:
            w_a, w_b = 1.0, 0.0
        else:
            wa_raw = 1.0 / (err_a * err_a + epsilon)
            wb_raw = 1.0 / (err_b * err_b + epsilon)
            s = wa_raw + wb_raw
            w_a = wa_raw / s
            w_b = wb_raw / s

        choose_a_for_jump = w_a >= w_b

        # Mélange des points de la fenêtre (même si un point est jump, on peut le lisser)
        for i in range(start, end):
            pa = points_a[i]
            pb = points_b[i]

            ts = pa.timestamp  # on suppose timestamps alignés
            x = w_a * pa.x + w_b * pb.x
            y = w_a * pa.y + w_b * pb.y

            if choose_a_for_jump:
                jump = pa.jump if w_a > w_b else (pa.jump or pb.jump)
            else:
                jump = pb.jump

            blended.append(Point(ts, x, y, jump))

    return blended

def ultimateSmooth(fenetre, points, calibration, reference, width, height, listeY):
    turboSmooth = calcTurboSmooth(fenetre, calibration, reference, points, width, height)
    calibratedSmooth = calcCalibratedLinesCoefSmooth(fenetre, calibration, reference, points, width, height)
    return blend_points_by_error(turboSmooth, calibratedSmooth, listeY)

def extraire_durees_mots(mots, pointsNormalized):

    listeMots = []

    for _, zone in mots.iterrows():
        x_min, x_max = zone["x"], zone["x"] + zone["largeur"]
        y_min, y_max = zone["y"], zone["y"] + zone["hauteur"]
        x_centre, y_centre = x_min + (zone["largeur"] / 2), y_min + (zone["hauteur"] / 2)
        mot = zone["mot"]

        # Filtrage des points à l’intérieur de la zone du mot
        times = [
            elem.timestamp
            for elem in pointsNormalized
            if x_min <= elem.x <= x_max and y_min <= elem.y + (zone["hauteur"] / 2) <= y_max
        ]

        if times:
            duree = times[-1] - times[0]
            listeMots.append((x_centre, y_centre, duree))
            # print(f"Mot: {mot} lu de {times[0]} à {times[-1]} soit {duree:.3f} secondes")

    return listeMots

def drawRect(fenetre, wordsDataFrame):
    for _, zone in wordsDataFrame.iterrows():
        pygame.draw.rect(fenetre, (255, 0, 0), (zone["x"], zone["y"], zone["largeur"], zone["hauteur"]), 2)


def getJumps(points, calibration, reference, width, height, nbLines, max_iterations = 15, fps = 30):
    print("Points total : ", len(points))
    returned_points = []
    avg_reading_speed = average_speed(points)
    print("Moyenne vitesse lecture :", avg_reading_speed)

    coefs = build_coef(calibration=calibration, reference=reference)

    # Aplatissement de la liste
    flat = [t for sublist in coefs for t in sublist]

    # Moyenne des distances euclidiennes
    moyenne = sum(math.hypot(x, y) for x, y in flat) / len(flat)
    print(moyenne)
    print("moyenne coeff ", moyenne)
    adjustedPoints = copy.deepcopy(points)
    width_coeff = getExtensionCoefs(coefs)
    print("Width_coeff ", width_coeff)
    height_coeff = 1
    optimal_number_points_jump = int((fps/4))
    nb_non_optimal_jumps = 0
    best_score_optimal_jumps = float("inf")
    index_array_readjusted_jumps = [None] * max_iterations
    array_non_optimal_difference = [None] * max_iterations
    for iteration in range(max_iterations):
        print("Start iteration")
        nb_non_optimal_jumps = 0
        optimal = True
        points, jumps = detectJumps(adjustedPoints, calibration, reference, width, height, avg_reading_speed, moyenne, width_coeff, height_coeff)
        ##On est plus strict lors de la détection de ligne  
        if (len(jumps) > nbLines - 1):
            height_coeff *= 1.15
        ##On détecte plus facilement une ligne
        elif (len(jumps) < nbLines - 1):
            height_coeff *= 0.85
        ##Cas où on a le bon nombre de sauts
        else:
            for jump in jumps:
                # longueur du saut
                jump_length = jump["end_index"] - jump["start_index"] + 1
                if jump_length > optimal_number_points_jump + 1:
                    optimal = False
                #TODO: check multiple points
                if (jump_length < int(fps/1.5)):
                    start_point = points[jump["start_index"]]
                    before_point = points[jump["start_index"] - 1]
                    if (before_point.x - start_point.x > 750 * width_coeff):
                        jump["start_index"] = jump["start_index"] - 1
                        before_point.jump = True
                        index_array_readjusted_jumps[iteration] = jump["start_index"]
                        if (iteration == 0 or index_array_readjusted_jumps[iteration] == index_array_readjusted_jumps[iteration-1]):
                            optimal = False
                            print("Non optimal")
                        print("⚠️ Readjusted ⚠️\n\n")
                added = max(0, jump_length - optimal_number_points_jump)
                nb_non_optimal_jumps += added

            array_non_optimal_difference[iteration] = nb_non_optimal_jumps
            if best_score_optimal_jumps > nb_non_optimal_jumps:
                best_score_optimal_jumps = nb_non_optimal_jumps

            returned_points = points

            if optimal is True:
                print("\n[ --- Found optimal jump configuration --- ]\n         ")
                break
        if (iteration == 0):
            returned_points = points
    print("Best score optimal jumps", best_score_optimal_jumps)

    return returned_points
def detectJumps(points, calibration, reference, width, height, average_speed, length_average, width_coeff=1, height_coeff=1):
    print("JUmp")
    listePoints = []
    jump_segments = []   # nouvelle liste : [{ "start_index": ..., "end_index": ... }, ...]

    if len(points) == 1:
        p = points[0]
        listePoints.append(Point(p.timestamp, p.x, p.y, False))
        return listePoints, jump_segments

    n = len(points)
    i = 0
    nb_sauts = 0

    while i < n - 1:
        jump, skip = isJumpNew(
            points[i],
            points[(i + 1):],
            None,
            None,
            average_speed,
            length_average,
            width_coef=width_coeff,
            height_coef=height_coeff
        )

        # On ajoute toujours le point courant comme "normal" par défaut
        listePoints.append(Point(points[i].timestamp, points[i].x, points[i].y, False))

        if not jump:
            # point normal (pas de saut)
            i += 1
            continue

        # Si on détecte un saut, on cherche le plus petit possible dans la même zone
        minSkipped = skip
        maxIndex = i + 1

        for index in range(i + 1, i + 1 + skip):
            if index >= len(points):
                break
            jumped, nbSkipped = isJumpNew(
                points[index],
                points[index:],
                None,
                None,
                average_speed,
                length_average,
                width_coeff,
                height_coeff
            )
            if jumped and nbSkipped < minSkipped:
                minSkipped = nbSkipped
                maxIndex = index

        nb_sauts += 1
        print(f"Saut #{nb_sauts} → taille : {minSkipped} points")

        # Calcul des indices de début / fin du saut dans la liste originale
        start_idx = maxIndex
        end_idx = min(maxIndex + minSkipped - 1, n - 1)  # inclus

        # On stocke le segment de saut
        jump_segments.append({
            "start_index": start_idx,
            "end_index": end_idx
        })

        # 1) points normaux entre i et maxIndex (exclu)
        for j in range(i + 1, maxIndex):
            if j >= len(points):
                break
            p = points[j]
            listePoints.append(Point(p.timestamp, p.x, p.y, False))  # normal

        # 2) points du saut
        for j in range(maxIndex, maxIndex + minSkipped):
            if j >= len(points):
                break
            p = points[j]
            listePoints.append(Point(p.timestamp, p.x, p.y, True))   # saut

        # 3) avancer
        i = maxIndex + minSkipped

    print(f"Nb sauts détectés : {nb_sauts}")

    # Dernier point s'il reste au moins un point
    if n > 0:
        last = points[-1]
        listePoints.append(Point(last.timestamp, last.x, last.y, False))

    # On retourne désormais la liste
    return listePoints, jump_segments

def countJumps(points):
    jump = False
    nb_jumps = 0

    for i in range(len(points)):
        # Si on entre dans une zone de jump
        if points[i].jump:
            jump = True

        # Si on sort d'une zone de jump → on compte un saut
        if jump and not points[i].jump:
            nb_jumps += 1
            jump = False

    print("Nb sauts :", nb_jumps)
    return nb_jumps

def getExtensionCoefs(coefs):
    firstCoef = coefs[0][0]
    lastCoef = coefs[0][-1]

    lastLineFirst = coefs[-1][0]
    lastLineLast = coefs[-1][-1]

    widthCoef = 1
    ##On check si sur chaque ligne on a bien une direction différente (donc aggrandissement, ou rappetitissement)
    ##En plus, on check si la première ligne et la dernière ont les mêmes directions
    if (firstCoef[0] * lastCoef[0] < 0 and lastLineFirst[0] * lastLineLast[0] < 0 and firstCoef[0] * lastLineFirst[0] > 0):
        moyenneCoef = (abs(firstCoef[0]) + abs(lastCoef[0]) + abs(lastLineFirst[0]) + abs(lastLineLast[0])) / 4
        #Valeur négative = trop petit
        #Valeur positive = trop grand
        if (firstCoef[0] < 0):
            widthCoef = 1 - ((moyenneCoef / 165) * 0.3)
        else:
            widthCoef = 1 + ((moyenneCoef / 165) * 0.3)
    return widthCoef


import pygame
import numpy as np
import cv2

def drawReadingQuad(fenetre, points, color=(255, 0, 0), thickness=2):
    pts = np.array([(p.x, p.y) for p in points], dtype=np.float32)

    if len(pts) < 3:
        return

    rect = cv2.minAreaRect(pts)
    box = cv2.boxPoints(rect)
    box = box.astype(int)  # ✔ Remplace np.int0

    for i in range(4):
        pygame.draw.line(
            fenetre,
            color,
            tuple(box[i]),
            tuple(box[(i + 1) % 4]),
            thickness
        )

def drawWordsQuad(fenetre, words, color=(0, 255, 0), thickness=2):
    """
    Calcule et dessine la plus petite box englobant tous les mots OCR.
    
    fenetre : surface pygame
    mots    : DataFrame avec colonnes x, y, largeur, hauteur
    """

    # On convertit tous les rectangles OCR en points (centre ou coins ? → coins)
    pts = []

    for _, w in words.iterrows():
        x, y = w["x"], w["y"]
        w_, h_ = w["largeur"], w["hauteur"]

        # 4 coins du mot
        pts.append((x,       y))
        pts.append((x+w_,    y))
        pts.append((x+w_,    y+h_))
        pts.append((x,       y+h_))

    pts = np.array(pts, dtype=np.float32)

    if len(pts) < 3:
        return

    # Calcul du rectangle minimal orienté contenant tous les mots
    rect = cv2.minAreaRect(pts)
    box = cv2.boxPoints(rect)
    box = box.astype(int)

    # Dessin du quadrilatère
    for i in range(4):
        pygame.draw.line(
            fenetre,
            color,
            tuple(box[i]),
            tuple(box[(i + 1) % 4]),
            thickness
        )

def _order_box_points(box):
    """
    Prend un quadrilatère (4 points) et renvoie les points
    dans l'ordre [haut-gauche, haut-droit, bas-droit, bas-gauche].
    """
    pts = np.array(box, dtype=np.float32)

    # somme x+y → tl = min, br = max
    s = pts.sum(axis=1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]

    # différence x-y → tr = min, bl = max
    diff = np.diff(pts, axis=1).ravel()
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]

    return np.array([tl, tr, br, bl], dtype=np.float32)


def compute_homography_reading_to_words(box_reading, box_words):
    """
    Calcule l'homographie H qui envoie la box de lecture (rouge)
    vers la box des mots OCR (verte).

    box_reading : iterable de 4 points (x, y) de la box rouge
    box_words   : iterable de 4 points (x, y) de la box verte

    retourne : matrice 3x3 (np.ndarray) d'homographie
    """
    src = _order_box_points(box_reading)
    dst = _order_box_points(box_words)

    H = cv2.getPerspectiveTransform(src, dst)
    return H


def apply_homography_to_points(points, H):
    """
    Applique l'homographie H à une liste d'objets avec attributs .x et .y.

    points : liste d'objets (ex. tes points de regard)
    H      : matrice 3x3 d'homographie

    Modifie les points **en place** (p.x, p.y) et les retourne.
    """
    if not points:
        return points

    pts = np.array([[p.x, p.y] for p in points], dtype=np.float32)
    pts = pts.reshape(-1, 1, 2)

    pts_warped = cv2.perspectiveTransform(pts, H).reshape(-1, 2)

    for p, (x_new, y_new) in zip(points, pts_warped):
        p.x = float(x_new)
        p.y = float(y_new)

    return points


def recalibrateReadingWithOCR(points, words, listeY):
    """
    Recalibre les points de regard en renvoyant une nouvelle liste de Point.
    - points : liste d'objets Point (originaux non modifiés)
    - words  : DataFrame OCR contenant x, y, largeur, hauteur
    - listeY : liste optionnelle avec la hauteur en Y de chaque ligne
    """

    # --- 1) Construire la box des points de regard (en ignorant le début) ---
    start_idx = _find_reading_start_index_direction(points)

    # On utilise seulement les points à partir de start_idx pour estimer la box
    pts_reading = np.array(
        [(p.x, p.y) for p in points[start_idx:]],
        dtype=np.float32
    )
    rect_reading = cv2.minAreaRect(pts_reading)
    box_reading = cv2.boxPoints(rect_reading)

    # --- 2) Construire la box OCR ---
    pts_words = []
    for _, w in words.iterrows():
        x, y = w["x"], w["y"]
        w_, h_ = w["largeur"], w["hauteur"]

        pts_words.append((x,      y))
        pts_words.append((x+w_,   y))
        pts_words.append((x+w_,   y+h_))
        pts_words.append((x,      y+h_))

    pts_words = np.array(pts_words, dtype=np.float32)
    rect_words = cv2.minAreaRect(pts_words)
    box_words = cv2.boxPoints(rect_words)

    # --- 3) Ordonner dans l'ordre TL, TR, BR, BL ---
    def order_box_points(box):
        box = np.array(box, dtype=np.float32)
        s = box.sum(axis=1)
        diff = np.diff(box, axis=1).ravel()

        tl = box[np.argmin(s)]
        br = box[np.argmax(s)]
        tr = box[np.argmin(diff)]
        bl = box[np.argmax(diff)]

        return np.array([tl, tr, br, bl], dtype=np.float32)

    src = order_box_points(box_reading)  # box regard
    dst = order_box_points(box_words)    # box texte

    # --- 4) Homographie regard → OCR ---
    H = cv2.getPerspectiveTransform(src, dst)

    # --- 5) Transformer TOUS les points sans modifier les originaux ---
    pts_all = np.array(
        [(p.x, p.y) for p in points],
        dtype=np.float32
    ).reshape(-1, 1, 2)

    pts_corrected_all = cv2.perspectiveTransform(pts_all, H).reshape(-1, 2)

    # Nouvelle liste d’objets Point corrigés (jump conservé 1:1)
    corrected_points = []
    for p, (x_new, y_new) in zip(points, pts_corrected_all):
        corrected_points.append(
            Point(
                timestamp=p.timestamp,
                x=float(x_new),
                y=float(y_new),
                jump=p.jump
            )
        )

    return corrected_points


def _find_reading_start_index_direction(points, max_skip=40, window_size=10, min_horizontal_ratio=1.5):
    """
    Détecte le début de la lecture en analysant la direction du mouvement.
    
    Règle :
      - si mouvement principalement VERS LA DROITE → début de lecture
      - si mouvement principalement VERS LE BAS → points parasites → on ignore
    
    min_horizontal_ratio : combien de fois le mouvement horizontal doit 
                           être supérieur au mouvement vertical.
    """

    n = len(points)
    if n <= window_size:
        return 0

    last_start = min(max_skip, n - window_size)

    for start in range(0, last_start + 1):
        p1 = points[start]
        p2 = points[start + window_size - 1]

        dx = p2.x - p1.x
        dy = p2.y - p1.y

        # On regarde le mouvement horizontal VS vertical
        # Si dx est attendu positif en lecture (droite)
        if dx > 0:
            # Le mouvement doit être "plus horizontal que vertical"
            if abs(dx) >= abs(dy) * min_horizontal_ratio:
                return start

        # Sinon : trop vertical → on ignore

    return 0

def drawReadingQuadFiltered(fenetre, points, color=(255, 0, 0), thickness=2):
    """
    Dessine la box de lecture, mais en ignorant les premiers points
    qui ne correspondent pas au début réel de la lecture.
    """

    # Trouver l'index où la lecture commence vraiment
    start_idx = _find_reading_start_index_direction(
        points
    )

    # On utilise les points filtrés pour la box
    usable_points = points[start_idx:]
    if len(usable_points) < 3:
        return

    pts = np.array([(p.x, p.y) for p in usable_points], dtype=np.float32)

    rect = cv2.minAreaRect(pts)
    box = cv2.boxPoints(rect)
    box = box.astype(int)

    # Dessiner la box dans pygame
    for i in range(4):
        pygame.draw.line(
            fenetre,
            color,
            tuple(box[i]),
            tuple(box[(i + 1) % 4]),
            thickness
        )

def adjust_lines(points, listeY, window_size=3):
    returned_points = []

    if not points:
        return returned_points

    segments = []
    current_segment = [points[0]]

    for p in points[1:]:
        if p.jump == current_segment[-1].jump:
            current_segment.append(p)
        else:
            segments.append(current_segment)
            current_segment = [p]
    segments.append(current_segment)

    for seg in segments:
        n = len(seg)
        for i, p in enumerate(seg):
            start = max(0, i - (window_size - 1))
            end = i + 1
            window = seg[start:end]

            # on garde x brut pour ne pas déformer l'ordre horizontal
            mean_x = p.x
            mean_y = sum(pp.y for pp in window) / len(window)

            if not p.jump and listeY:
                closest_y = min(listeY, key=lambda ly: abs(ly - mean_y))
                y_snapped = closest_y
            else:
                y_snapped = mean_y

            returned_points.append(
                Point(
                    timestamp=p.timestamp,
                    x=mean_x,
                    y=y_snapped,
                    jump=p.jump
                )
            )

    return returned_points



if __name__ == "__main__":
    main()

#TODO: Prendre la liste des points, et remettre sur chaque début de ligne
#réduire le changement en Y ? 
