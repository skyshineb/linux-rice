import QtQuick 2.15
import QtQuick.Controls 2.5 as QQC2
import org.kde.kirigami 2.5 as Kirigami

Kirigami.FormLayout {
    anchors.left: parent.left
    anchors.right: parent.right

    property alias cfg_maxRpm: speedSpin.value

    QQC2.SpinBox {
        id: speedSpin
        Kirigami.FormData.label: i18n("Maximum speed at 100% CPU (RPM):")
        from: 0
        to: 120
        stepSize: 1
        editable: true
    }
}
