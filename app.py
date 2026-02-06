from flask import Flask, render_template

from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from cli import register_commands
    register_commands(app)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        from models import Report

        reports = Report.query.order_by(Report.created_at.desc()).all()
        return render_template("index.html", reports=reports)

    @app.route("/post/<int:report_id>")
    def post(report_id):
        from models import Report

        report = Report.query.get_or_404(report_id)
        return render_template("post.html", report=report)

    @app.route("/about")
    def about():
        return render_template("about.html")

    return app


app = create_app()
