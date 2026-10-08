# --- импорты ---
from datetime import date, datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
    flash,
)

# --- приложение ---
app = Flask(__name__)
app.secret_key = "stellaris-dev-key"

# --- данные ---
MISSIONS = [
    {
        "id": 1,
        "slug": "luna",
        "planet": "Луна",
        "company": "NASA · Artemis",
        "title": "Артемида: возвращение на Луну",
        "launch": "2031",
        "image": "moon.png",
        "short": "Первая постоянная база в кратере Шеклтон.",
        "status": "active",
        "description": (
            "Программа Artemis — международная инициатива NASA "
            "по возвращению человека на Луну и созданию первой "
            "долговременной базы у южного полюса. Кратер Шеклтон "
            "выбран из-за залежей водяного льда, пригодного для "
            "производства топлива и жизнеобеспечения. База рассчитана "
            "на постоянное проживание экипажа из 4 человек с "
            "ротацией каждые 6 месяцев."
        ),
    },
    {
        "id": 2,
        "slug": "mars",
        "planet": "Марс",
        "company": "SpaceX · Starship",
        "title": "Арес: первый город",
        "launch": "2033",
        "image": "mars.png",
        "short": "Первая самоокупаемая колония на Марсе.",
        "status": "active",
        "description": (
            "Цель SpaceX — сделать человечество межпланетным видом. "
            "Корабль Starship способен доставить до 100 человек "
            "и 100 тонн груза за один рейс. Первые беспилотные "
            "миссии запланированы на конец 2020-х, пилотируемые — "
            "на начало 2030-х. Колония должна стать самоокупаемой "
            "за счёт добычи ресурсов на месте и производства топлива "
            "из марсианской атмосферы."
        ),
    },
    {
        "id": 3,
        "slug": "venus",
        "planet": "Венера",
        "company": "NASA · VERITAS",
        "title": "Афродита: парящий город",
        "launch": "2040",
        "image": "venus.png",
        "short": "Аэростатные платформы в верхних слоях атмосферы.",
        "status": "planned",
        "description": (
            "Венера — ближайшая к Земле планета, но её поверхность "
            "раскалена до +460 °C, а давление в 90 раз выше земного. "
            "Однако на высоте 50 км атмосфера по давлению и "
            "температуре близка к земной. Концепция «парящих городов» "
            "предполагает аэростатные платформы, постоянно дрейфующие "
            "в верхних слоях. Миссия VERITAS займётся картографированием "
            "и изучением атмосферы перед пилотируемым этапом."
        ),
    },
]

APPLICATIONS = []
NEXT_APPLICATION_ID = 1

# --- вспомогательные функции ---
def get_mission_by_id(mission_id):
    for m in MISSIONS:
        if m["id"] == mission_id:
            return m
    return None


def get_application_by_id(app_id):
    for a in APPLICATIONS:
        if a["id"] == app_id:
            return a
    return None


# --- главная ---
@app.route("/")
def index():
    planets_count = 3
    colonists_count = 8_000_000_000
    active_missions_count = sum(1 for m in MISSIONS if m["status"] == "active")
    active_missions = [m for m in MISSIONS if m["status"] == "active"]
    return render_template(
        "index.html",
        planets_count=planets_count,
        colonists_count=colonists_count,
        active_missions_count=active_missions_count,
        active_missions=active_missions,
    )


# --- миссии ---
@app.route("/missions")
def missions():
    planet_filter = request.args.get("planet", "")
    filtered = MISSIONS
    if planet_filter:
        filtered = [m for m in MISSIONS if m["planet"] == planet_filter]
    planets = ["Луна", "Марс", "Венера"]
    return render_template(
        "missions.html",
        missions=filtered,
        planets=planets,
        current_filter=planet_filter,
    )


@app.route("/missions/<int:mission_id>")
def mission_detail(mission_id):
    mission = get_mission_by_id(mission_id)
    if mission is None:
        abort(404)
    return render_template("mission_detail.html", mission=mission)


# --- о проекте ---
@app.route("/about")
def about():
    return render_template("about.html")


# --- заявка (GET + POST) ---
@app.route("/apply/<int:mission_id>", methods=["GET", "POST"])
def apply(mission_id):
    mission = get_mission_by_id(mission_id)
    if mission is None:
        abort(404)

    if request.method == "GET":
        return render_template("apply.html", mission=mission, form_data={}, min_date=date.today().isoformat())

    # POST
    global NEXT_APPLICATION_ID

    commander = request.form.get("commander", "").strip()
    crew_size = request.form.get("crew_size", "").strip()
    launch_date = request.form.get("launch_date", "").strip()
    goal = request.form.get("goal", "").strip()

    errors = []

    if not commander:
        errors.append("Укажите имя командира.")

    try:
        crew_size_int = int(crew_size)
        if crew_size_int < 1 or crew_size_int > 20:
            errors.append("Размер экипажа должен быть числом от 1 до 20.")
    except ValueError:
        errors.append("Размер экипажа должен быть числом от 1 до 20.")

    try:
        d = datetime.strptime(launch_date, "%Y-%m-%d").date()
        if d < date.today():
            errors.append("Дата запуска не может быть в прошлом.")
    except ValueError:
        errors.append("Некорректная дата.")

    if not goal or len(goal) < 10:
        errors.append("Опишите цель миссии (минимум 10 символов).")

    if errors:
        return render_template(
            "apply.html",
            mission=mission,
            errors=errors,
            form_data=request.form,
            min_date=date.today().isoformat(),
        )

    application = {
        "id": NEXT_APPLICATION_ID,
        "mission_id": mission_id,
        "commander": commander,
        "crew_size": int(crew_size),
        "launch_date": launch_date,
        "goal": goal,
    }
    APPLICATIONS.append(application)
    NEXT_APPLICATION_ID += 1

    flash("Заявка успешно подана!")
    return redirect(url_for("application", app_id=application["id"]))


# --- результат ---
@app.route("/application/<int:app_id>")
def application(app_id):
    application = get_application_by_id(app_id)
    if application is None:
        abort(404)
    mission = get_mission_by_id(application["mission_id"])
    return render_template(
        "application.html", application=application, mission=mission
    )


# --- 404 ---
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# --- запуск ---
if __name__ == "__main__":
    app.run(debug=True, port=5001)
